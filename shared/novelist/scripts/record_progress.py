from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_returns(values: list[str]) -> dict[str, str]:
    returns: dict[str, str] = {}
    for value in values:
        character_id, separator, reason = value.partition("=")
        if not separator or not character_id or not reason.strip():
            raise ValueError("returns must use character-id=reason")
        returns[character_id] = reason.strip()
    return returns


def record(
    project: Path,
    chapter: int,
    title: str,
    summary: str,
    present_ids: list[str],
    returns: dict[str, str],
) -> None:
    story_path = project / "story.json"
    progress_path = project / "progress.json"
    state_path = project / "state.json"
    characters_path = project / "characters.json"
    story = read_json(story_path)
    progress = read_json(progress_path)
    state = read_json(state_path)
    registry = read_json(characters_path)
    characters = {character["id"]: character for character in registry["characters"]}

    expected = progress["latest_accepted_chapter"] + 1
    if chapter != expected:
        raise ValueError(f"expected chapter {expected}, got {chapter}")
    unknown = set(present_ids) - characters.keys()
    if unknown:
        raise ValueError(f"unknown character IDs: {', '.join(sorted(unknown))}")
    invalid_returns = returns.keys() - set(present_ids)
    if invalid_returns:
        raise ValueError(f"returning characters must be present: {', '.join(sorted(invalid_returns))}")
    unapproved = {
        character_id
        for character_id in present_ids
        if characters[character_id]["status"] != "active" and character_id not in returns
    }
    if unapproved:
        raise ValueError(f"non-active characters require --return: {', '.join(sorted(unapproved))}")

    for character_id in present_ids:
        character = characters[character_id]
        if character_id in returns:
            character["status"] = "active"
        character["last_seen_chapter"] = chapter
        character["last_event"] = summary

    entry = {
        "chapter": chapter,
        "title": title,
        "summary": summary,
        "present_character_ids": present_ids,
        "character_returns": returns,
    }
    progress["latest_accepted_chapter"] = chapter
    progress["latest_summary"] = summary
    progress["active_character_ids"] = present_ids
    progress["chapter_history"].append(entry)
    story["current_chapter"] = chapter
    story["latest_progress"] = summary
    state["current_chapter"] = chapter

    write_json(story_path, story)
    write_json(progress_path, progress)
    write_json(state_path, state)
    write_json(characters_path, registry)


def main() -> int:
    parser = argparse.ArgumentParser(description="Record an accepted chapter and character appearances")
    parser.add_argument("project", type=Path)
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--present", action="append", default=[])
    parser.add_argument("--return", dest="returns", action="append", default=[])
    args = parser.parse_args()
    try:
        record(
            args.project.resolve(),
            args.chapter,
            args.title,
            args.summary,
            args.present,
            parse_returns(args.returns),
        )
    except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as error:
        parser.error(str(error))
    print(f"Recorded chapter {args.chapter}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())