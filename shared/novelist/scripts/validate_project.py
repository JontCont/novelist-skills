from __future__ import annotations

import argparse
import json
from pathlib import Path

from locale_config import load_config


REQUIRED_PATHS = (
    "constitution.md",
    "checklists/requirements.md",
    ".novelist/config.json",
    "spec.md",
    "state.json",
    "story.json",
    "characters.json",
    "progress.json",
    "canon/world.md",
    "canon/characters.md",
    "canon/timeline.md",
    "canon/setups.md",
    "outline/outline.md",
    "chapters/tasks",
    "chapters/drafts",
    "chapters/summaries",
)
REQUIRED_STATE_KEYS = {"title", "slug", "stage", "current_chapter"}
CHARACTER_STATUSES = {"active", "dead", "departed", "missing"}
REQUIRED_CHARACTER_KEYS = {
    "id",
    "name",
    "aliases",
    "role",
    "personality",
    "status",
    "current_location",
    "first_appearance_chapter",
    "last_seen_chapter",
    "last_event",
    "return_condition",
}


def validate(project: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_PATHS:
        if not (project / relative).exists():
            errors.append(f"missing: {relative}")

    state_path = project / "state.json"
    if state_path.is_file():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            errors.append(f"invalid state.json: {error}")
        else:
            for key in sorted(REQUIRED_STATE_KEYS - state.keys()):
                errors.append(f"state.json missing key: {key}")
            if not isinstance(state.get("current_chapter"), int) or state.get("current_chapter", -1) < 0:
                errors.append("state.json current_chapter must be a non-negative integer")

    spec_path = project / "spec.md"
    if spec_path.is_file():
        spec = spec_path.read_text(encoding="utf-8")
        if "{{" in spec or "待確認" in spec or "[NEEDS CLARIFICATION" in spec:
            errors.append("spec.md contains unresolved decisions")

    characters_path = project / "characters.json"
    if characters_path.is_file():
        try:
            registry = json.loads(characters_path.read_text(encoding="utf-8"))
            characters = registry["characters"]
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as error:
            errors.append(f"invalid characters.json: {error}")
        else:
            if not isinstance(characters, list):
                errors.append("characters.json characters must be an array")
            else:
                seen_ids: set[str] = set()
                for index, character in enumerate(characters):
                    if not isinstance(character, dict):
                        errors.append(f"characters.json character {index} must be an object")
                        continue
                    missing = REQUIRED_CHARACTER_KEYS - character.keys()
                    for key in sorted(missing):
                        errors.append(f"characters.json character {index} missing key: {key}")
                    character_id = character.get("id")
                    if character_id in seen_ids:
                        errors.append(f"characters.json duplicate id: {character_id}")
                    elif isinstance(character_id, str):
                        seen_ids.add(character_id)
                    if character.get("status") not in CHARACTER_STATUSES:
                        errors.append(f"characters.json character {index} has invalid status")

    try:
        config = load_config(project)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
        errors.append(f"invalid .novelist/config.json: {error}")
    else:
        locale = config["content_locale"]
        for relative in ("state.json", "story.json"):
            path = project / relative
            if path.is_file():
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if value.get("content_locale") != locale:
                    errors.append(f"{relative} content_locale must match .novelist/config.json")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a novel project")
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    errors = validate(args.project.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Novel project structure is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())