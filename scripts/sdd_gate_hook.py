from __future__ import annotations

import json
import re
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPTS = PLUGIN_ROOT / "shared/novelist/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from sdd import check, gate  # noqa: E402
from sdd_core import BASE_APPROVALS  # noqa: E402


WRITE_TOOL_MARKERS = ("apply", "create", "edit", "replace", "write", "terminal")


def iter_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def target_paths(tool_name: str, tool_input: object, cwd: Path) -> list[Path]:
    found: set[Path] = set()
    candidates: list[str] = []
    if isinstance(tool_input, dict):
        for key, value in tool_input.items():
            if key.lower() in {"filepath", "file_path", "path"} and isinstance(value, str):
                candidates.append(value)
    for value in iter_strings(tool_input):
        candidates.extend(
            match.group(1).strip()
            for match in re.finditer(r"(?m)^\*\*\* (?:Add|Update|Delete) File:\s*(.+)$", value)
        )
        if "terminal" in tool_name:
            normalized = value.replace("\\", "/")
            candidates.extend(
                re.findall(r"(?:[A-Za-z]:/[^\r\n\"]+|novels/[^\s\"]+)", normalized, re.IGNORECASE)
            )
    for value in candidates:
        candidate = Path(value.strip().strip("\"").rstrip("*).,;"))
        found.add(candidate.resolve() if candidate.is_absolute() else (cwd / candidate).resolve())
    return sorted(found)


def relative_novel_path(path: Path) -> str:
    normalized = path.as_posix()
    marker = "/novels/"
    return normalized.partition(marker)[2] if marker in normalized else ""


def novel_project(path: Path) -> Path | None:
    for parent in path.parents:
        if parent.parent.name.lower() == "novels":
            return parent
    return None


def phase_dependencies(relative: str) -> tuple[str, ...]:
    if relative == "spec.md":
        return ("constitution.md",)
    if relative in {"story.json", "characters.json"} or relative.startswith("canon/"):
        return ("constitution.md", "spec.md")
    if relative.startswith("outline/"):
        return BASE_APPROVALS[:-1]
    if relative.startswith("chapters/tasks/"):
        return BASE_APPROVALS
    return ()


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        print(f"Novel SDD hook received invalid JSON: {error}", file=sys.stderr)
        return 2

    tool_name = str(event.get("tool_name", "")).lower()
    if not any(marker in tool_name for marker in WRITE_TOOL_MARKERS):
        return 0
    cwd = Path(event.get("cwd") or Path.cwd()).resolve()
    targets = target_paths(tool_name, event.get("tool_input", {}), cwd)
    protected: list[str] = []
    for target in targets:
        relative = relative_novel_path(target)
        if "/checklists/" in f"/{relative}" and relative.endswith(".md"):
            protected.append(f"reviewer-owned checklist: {target}")
        elif relative.endswith("/.novelist/approvals.json"):
            protected.append(f"managed approval store: {target}")
        elif "/.novelist/retrievals/" in f"/{relative}" and relative.endswith(".json"):
            protected.append(f"managed RAG receipt: {target}")
    if protected:
        print(
            "Novel SDD governance blocked direct modification; use reviewer action or the managed CLI. "
            + " | ".join(protected),
            file=sys.stderr,
        )
        return 2

    blocked: list[str] = []
    for draft in targets:
        relative_with_slug = relative_novel_path(draft)
        project = novel_project(draft)
        if not relative_with_slug or project is None:
            continue
        relative = draft.relative_to(project).as_posix()
        if relative.startswith("chapters/drafts/") and draft.suffix.lower() == ".md":
            errors = gate(project, f"chapters/tasks/{draft.stem}.md")
        else:
            errors = []
            for dependency in phase_dependencies(relative):
                try:
                    check(project, dependency)
                except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as error:
                    errors.append(str(error))
        if errors:
            blocked.append(f"{draft}: " + "; ".join(errors))
    if blocked:
        print(
            "Novel SDD gate blocked draft modification. " + " | ".join(blocked),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
