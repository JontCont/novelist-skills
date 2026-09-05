from __future__ import annotations

import argparse
import json
from pathlib import Path


UNAVAILABLE_STATUSES = {"dead", "departed", "missing"}


def load_characters(project: Path) -> list[dict]:
    registry = json.loads((project / "characters.json").read_text(encoding="utf-8"))
    return registry["characters"]


def find_unplanned_returns(characters: list[dict], prose: str, allowed: set[str]) -> list[str]:
    errors: list[str] = []
    for character in characters:
        names = [character["name"], *character.get("aliases", [])]
        appears = any(name and name in prose for name in names)
        if appears and character["status"] in UNAVAILABLE_STATUSES and character["id"] not in allowed:
            errors.append(
                f"{character['name']} ({character['id']}) is {character['status']} "
                f"after chapter {character['last_seen_chapter']}; approve the return explicitly"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Check character appearances in a chapter draft")
    parser.add_argument("project", type=Path)
    parser.add_argument("draft", type=Path)
    parser.add_argument("--allow-return", action="append", default=[])
    args = parser.parse_args()

    try:
        characters = load_characters(args.project.resolve())
        prose = args.draft.read_text(encoding="utf-8")
    except (FileNotFoundError, json.JSONDecodeError, KeyError, UnicodeDecodeError) as error:
        parser.error(str(error))
    known_ids = {character["id"] for character in characters}
    unknown_allowed = set(args.allow_return) - known_ids
    if unknown_allowed:
        parser.error(f"unknown character IDs: {', '.join(sorted(unknown_allowed))}")

    errors = find_unplanned_returns(characters, prose, set(args.allow_return))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("Character appearance continuity passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
