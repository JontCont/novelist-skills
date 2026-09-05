from __future__ import annotations

import hashlib
import json
from pathlib import Path


SEARCH_ROOTS = (
    ".novelist/config.json",
    "constitution.md",
    "checklists",
    "story.json",
    "characters.json",
    "progress.json",
    "spec.md",
    "canon",
    "outline",
    "chapters/tasks",
    "chapters/summaries",
    "research",
)
BASE_APPROVALS = (
    "constitution.md",
    "spec.md",
    "characters.json",
    "canon/world.md",
    "canon/characters.md",
    "canon/timeline.md",
    "canon/setups.md",
    "outline/outline.md",
)


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def iter_knowledge_files(project: Path):
    for relative in SEARCH_ROOTS:
        target = project / relative
        if target.is_file():
            yield target
        elif target.is_dir():
            yield from sorted(
                path for path in target.rglob("*") if path.suffix.lower() in {".md", ".txt", ".json"}
            )


def corpus_hash(project: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(iter_knowledge_files(project)):
        digest.update(path.relative_to(project).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def approvals_path(project: Path) -> Path:
    return project / ".novelist/approvals.json"


def read_approvals(project: Path) -> dict:
    return json.loads(approvals_path(project).read_text(encoding="utf-8"))


def artifact_is_current(project: Path, relative: str, approvals: dict) -> bool:
    path = project / relative
    approved = approvals.get("artifacts", {}).get(relative)
    return path.is_file() and approved is not None and approved.get("sha256") == file_hash(path)
