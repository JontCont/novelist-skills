from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from locale_config import load_config
from sdd_core import BASE_APPROVALS, approvals_path, artifact_is_current, corpus_hash, file_hash, read_approvals
from validate_project import validate


CANON_APPROVALS = (
    "characters.json",
    "canon/world.md",
    "canon/characters.md",
    "canon/timeline.md",
    "canon/setups.md",
)
CLARIFICATION_MARKERS = ("[NEEDS CLARIFICATION", "{{", "待確認")


def has_substantive_content(path: Path) -> bool:
    ignored_table_headers = ("| When | Event | Source |", "| ID | Setup | Status | Intended payoff | Source |")
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if not value or value.startswith("#") or value in ignored_table_headers:
            continue
        if value.startswith("| ---"):
            continue
        return True
    return False


def readiness_errors(project: Path, relative: str) -> list[str]:
    path = project / relative
    errors: list[str] = []
    if relative == "constitution.md":
        text = path.read_text(encoding="utf-8")
        if "## Governance" not in text or "MUST" not in text or any(marker in text for marker in CLARIFICATION_MARKERS):
            errors.append("constitution.md must contain binding principles and governance")
    elif relative == "spec.md":
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in CLARIFICATION_MARKERS):
            errors.append("spec.md still contains unresolved decisions")
        errors.extend(checklist_errors(project))
    elif relative == "characters.json":
        registry = json.loads(path.read_text(encoding="utf-8"))
        characters = registry.get("characters", [])
        if not characters:
            errors.append("characters.json must register at least one character")
        if not any(character.get("role") == "protagonist" for character in characters):
            errors.append("characters.json must register a protagonist")
        protagonist_ids = json.loads((project / "story.json").read_text(encoding="utf-8")).get("protagonist_ids", [])
        known_ids = {character.get("id") for character in characters}
        if not protagonist_ids or not set(protagonist_ids).issubset(known_ids):
            errors.append("story.json protagonist_ids must reference registered characters")
    elif relative == "outline/outline.md":
        text = path.read_text(encoding="utf-8")
        if "## Constitution Check" not in text or "- [ ]" in text:
            errors.append("outline must contain a completed Constitution Check")
        if not has_substantive_content(path):
            errors.append(f"{relative} has no substantive content")
    elif relative.startswith("canon/"):
        if not has_substantive_content(path):
            errors.append(f"{relative} has no substantive content")
    elif relative.startswith("chapters/tasks/"):
        text = path.read_text(encoding="utf-8")
        required_fields = (
            "Viewpoint",
            "Time and location",
            "Outline reference",
            "Chapter goal",
            "Opposition",
            "Emotional movement",
            "New situation",
            "Character state changes",
            "Knowledge revealed or concealed",
            "Next pressure",
        )
        for field in required_fields:
            if not re.search(rf"(?m)^- {re.escape(field)}:\s+\S", text):
                errors.append(f"chapter task missing value: {field}")
        retrieval = text.partition("## Retrieval Query")[2].strip()
        if not retrieval:
            errors.append("chapter task must include a retrieval query")
        beats = text.partition("## Required Beats")[2].partition("##")[0]
        if not re.search(r"(?m)^\d+\.\s+\S", beats):
            errors.append("chapter task must include at least one required beat")
    return errors


def checklist_errors(project: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((project / "checklists").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if re.search(r"(?m)^\s*- \[ \]", text):
            errors.append(f"checklist is incomplete: {path.relative_to(project).as_posix()}")
    return errors


def analyze(project: Path, task_relative: str) -> list[str]:
    errors = checklist_errors(project)
    try:
        approvals = read_approvals(project)
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as error:
        return [f"cannot read approvals: {error}"]
    for relative in (*BASE_APPROVALS, task_relative):
        if not artifact_is_current(project, relative, approvals):
            errors.append(f"analysis prerequisite is missing approval or stale: {relative}")
    paths = [project / "constitution.md", project / "spec.md", project / "outline/outline.md", project / task_relative]
    for path in paths:
        if not path.is_file():
            errors.append(f"analysis input is missing: {path.relative_to(project).as_posix()}")
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in CLARIFICATION_MARKERS):
            errors.append(f"analysis found unresolved marker: {path.relative_to(project).as_posix()}")

    task_path = project / task_relative
    characters_path = project / "characters.json"
    if task_path.is_file() and characters_path.is_file():
        task_text = task_path.read_text(encoding="utf-8")
        viewpoint_match = re.search(r"(?m)^- Viewpoint:\s+(.+)$", task_text)
        characters = json.loads(characters_path.read_text(encoding="utf-8")).get("characters", [])
        known_names = {name for character in characters for name in [character.get("name"), *character.get("aliases", [])] if name}
        if viewpoint_match and viewpoint_match.group(1).strip() not in known_names:
            errors.append("chapter task viewpoint is not a registered character")
    return errors


def required_dependencies(relative: str) -> tuple[str, ...]:
    if relative == "constitution.md":
        return ()
    if relative == "spec.md":
        return ("constitution.md",)
    if relative in CANON_APPROVALS:
        return ("constitution.md", "spec.md")
    if relative == "outline/outline.md":
        return ("constitution.md", "spec.md", *CANON_APPROVALS)
    if relative.startswith("chapters/tasks/"):
        return BASE_APPROVALS
    return ()


def invalidate_downstream(approvals: dict, relative: str) -> None:
    artifacts = approvals["artifacts"]
    if relative == "spec.md":
        stale = set(artifacts) - {"constitution.md", relative}
    elif relative == "constitution.md":
        stale = set(artifacts) - {relative}
    elif relative in CANON_APPROVALS:
        stale = {name for name in artifacts if name == "outline/outline.md" or name.startswith("chapters/tasks/")}
    elif relative == "outline/outline.md":
        stale = {name for name in artifacts if name.startswith("chapters/tasks/")}
    else:
        stale = set()
    for name in stale:
        artifacts.pop(name, None)


def normalize_artifact(project: Path, artifact: str) -> str:
    path = (project / artifact).resolve()
    try:
        relative = path.relative_to(project).as_posix()
    except ValueError as error:
        raise ValueError("artifact must be inside the novel project") from error
    allowed = relative in BASE_APPROVALS or relative.startswith("chapters/tasks/")
    if not allowed or not path.is_file():
        raise ValueError(f"artifact cannot be approved: {relative}")
    return relative


def approve(project: Path, artifact: str) -> str:
    relative = normalize_artifact(project, artifact)
    approvals = read_approvals(project)
    errors = readiness_errors(project, relative)
    for dependency in required_dependencies(relative):
        if not artifact_is_current(project, dependency, approvals):
            errors.append(f"dependency is missing approval or stale: {dependency}")
    if errors:
        raise ValueError("; ".join(errors))
    invalidate_downstream(approvals, relative)
    approvals["artifacts"][relative] = {
        "sha256": file_hash(project / relative),
        "approved_at": datetime.now(timezone.utc).isoformat(),
    }
    approvals_path(project).write_text(
        json.dumps(approvals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return relative


def check(project: Path, artifact: str) -> str:
    relative = normalize_artifact(project, artifact)
    approvals = read_approvals(project)
    if not artifact_is_current(project, relative, approvals):
        raise ValueError(f"artifact is missing approval or stale: {relative}")
    return relative


def gate(project: Path, task: str) -> list[str]:
    errors = validate(project)
    try:
        task_relative = normalize_artifact(project, task)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as error:
        return [str(error)]

    errors.extend(analyze(project, task_relative))

    receipt_path = project / ".novelist/retrievals" / f"{Path(task_relative).stem}.json"
    if not receipt_path.is_file():
        errors.append(f"missing RAG receipt: {receipt_path.relative_to(project).as_posix()}")
    else:
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            errors.append(f"invalid RAG receipt: {error}")
        else:
            if receipt.get("task") != task_relative:
                errors.append("RAG receipt belongs to another chapter task")
            if receipt.get("task_sha256") != file_hash(project / task_relative):
                errors.append("RAG receipt chapter task is stale")
            if receipt.get("corpus_sha256") != corpus_hash(project):
                errors.append("RAG receipt knowledge corpus is stale")
            if receipt.get("content_locale") != load_config(project)["content_locale"]:
                errors.append("RAG receipt locale is stale")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage strict novel SDD gates")
    subparsers = parser.add_subparsers(dest="command", required=True)
    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("project", type=Path)
    approve_parser.add_argument("artifact")
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("project", type=Path)
    check_parser.add_argument("artifact")
    gate_parser = subparsers.add_parser("gate")
    gate_parser.add_argument("project", type=Path)
    gate_parser.add_argument("--task", required=True)
    analyze_parser = subparsers.add_parser("analyze")
    analyze_parser.add_argument("project", type=Path)
    analyze_parser.add_argument("--task", required=True)
    args = parser.parse_args()
    project = args.project.resolve()

    try:
        load_config(project)
        if args.command == "approve":
            relative = approve(project, args.artifact)
            print(f"Approved {relative}.")
            return 0
        if args.command == "check":
            relative = check(project, args.artifact)
            print(f"Approval is current: {relative}.")
            return 0
        errors = analyze(project, normalize_artifact(project, args.task)) if args.command == "analyze" else gate(project, args.task)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as error:
        parser.error(str(error))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("SDD analysis passed." if args.command == "analyze" else "SDD drafting gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
