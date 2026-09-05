from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from locale_config import default_config, locale_description, normalize_locale


CANON_FILES = {
    "world.md": "# World Canon\n\n## Rules\n\n## Locations\n\n## Factions\n\n## Terminology\n",
    "characters.md": "# Character Canon\n\n## Main Characters\n\n## Relationships\n\n## Character Knowledge\n",
    "timeline.md": "# Timeline Canon\n\n| When | Event | Source |\n| --- | --- | --- |\n",
    "setups.md": "# Setups and Payoffs\n\n| ID | Setup | Status | Intended payoff | Source |\n| --- | --- | --- | --- | --- |\n",
}


def valid_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise argparse.ArgumentTypeError("slug must use lowercase letters, numbers, and hyphens")
    return value


def create_project(root: Path, slug: str, title: str, locale: str = "zh-Hant") -> Path:
    locale = normalize_locale(locale)
    project = root / "novels" / slug
    if project.exists():
        raise FileExistsError(f"project already exists: {project}")

    for directory in (
        ".novelist/retrievals",
        "checklists",
        "canon",
        "outline",
        "chapters/tasks",
        "chapters/drafts",
        "chapters/summaries",
        "research",
    ):
        (project / directory).mkdir(parents=True, exist_ok=True)

    templates = Path(__file__).resolve().parents[1] / "assets/templates"
    language, orthography = locale_description(locale)
    spec = (templates / "spec.md").read_text(encoding="utf-8")
    spec = spec.replace("{{TITLE}}", title).replace("{{LANGUAGE}}", language).replace("{{ORTHOGRAPHY}}", orthography)
    (project / "spec.md").write_text(spec, encoding="utf-8")
    (project / "constitution.md").write_text(
        (templates / "constitution.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (project / "checklists/requirements.md").write_text(
        (templates / "requirements-checklist.md").read_text(encoding="utf-8"), encoding="utf-8"
    )
    for name, content in CANON_FILES.items():
        (project / "canon" / name).write_text(content, encoding="utf-8")
    outline = (templates / "outline.md").read_text(encoding="utf-8").replace("{{TITLE}}", title)
    (project / "outline/outline.md").write_text(outline, encoding="utf-8")
    state = {"title": title, "slug": slug, "stage": "discovery", "current_chapter": 0, "content_locale": locale}
    (project / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    story = {
        "title": title,
        "content_locale": locale,
        "protagonist_ids": [],
        "current_chapter": 0,
        "latest_progress": "尚未開始",
    }
    (project / "story.json").write_text(
        json.dumps(story, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (project / "characters.json").write_text(
        json.dumps({"characters": []}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    progress = {
        "latest_accepted_chapter": 0,
        "latest_summary": "尚未開始",
        "active_character_ids": [],
        "chapter_history": [],
    }
    (project / "progress.json").write_text(
        json.dumps(progress, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    approvals = {"version": 1, "artifacts": {}}
    (project / ".novelist/approvals.json").write_text(
        json.dumps(approvals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (project / ".novelist/config.json").write_text(
        json.dumps(default_config(locale), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return project


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a specification-driven novel project")
    parser.add_argument("slug", type=valid_slug)
    parser.add_argument("--title", required=True)
    parser.add_argument("--locale", default="zh-Hant")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    try:
        project = create_project(args.root.resolve(), args.slug, args.title.strip(), args.locale)
    except (FileExistsError, FileNotFoundError, ValueError) as error:
        parser.error(str(error))
    print(project)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
