# Artifact Contract

Each novel is a directory under `novels/<slug>/`. These files are the durable
state of the writing project and replace assumptions held only in chat.

## Required artifacts

| Path | Role |
| --- | --- |
| `constitution.md` | Binding creative principles and governance; outranks all other artifacts |
| `spec.md` | User intent, genre, scope, tone, boundaries, premise, ending contract |
| `checklists/requirements.md` | Reviewer-owned specification quality gate |
| `canon/world.md` | World rules, locations, factions, terminology |
| `canon/characters.md` | Character identities, goals, knowledge, relationships, arcs |
| `canon/timeline.md` | Chronological events and relative timing |
| `canon/setups.md` | Setups, clues, promises, status, and intended payoff |
| `outline/outline.md` | Story structure and chapter-level progression |
| `state.json` | Current stage, approved chapter, and project metadata |
| `story.json` | Novel title, protagonist IDs, current chapter, latest progress |
| `characters.json` | Structured personality and appearance lifecycle for every character |
| `progress.json` | Latest accepted summary, active cast, and chapter history |

Create these directories as work begins:

- `chapters/tasks/`: one approved specification per chapter.
- `chapters/drafts/`: prose drafts; drafts are not canon by themselves.
- `chapters/summaries/`: accepted chapter outcomes and state changes.
- `research/`: optional source notes, separated from fictional canon.

## Authority order

When facts conflict, use this order:

1. Explicit decisions in `canon/`.
2. Approved chapter summaries.
3. Approved outline and chapter tasks.
4. Draft prose.
5. Open ideas from conversation.

Do not resolve a conflict by guessing. Report both sources and ask the user to
choose, then update the authoritative artifact.

## Character lifecycle

Register every named character in `characters.json` before drafting their first
appearance. Each character has these fields:

- `id`: stable kebab-case identifier; never reuse it for another person.
- `name` and `aliases`: names that the continuity checker can find in prose.
- `role`: `protagonist`, `supporting`, `antagonist`, or `minor`.
- `personality`: stable behavioral traits and contradictions.
- `status`: `active`, `dead`, `departed`, or `missing`.
- `current_location`, `first_appearance_chapter`, `last_seen_chapter`, and
   `last_event`: the latest accepted state.
- `return_condition`: established condition required for a plausible return,
   or `null` when none has been established.

Before accepting a chapter, run `scripts/check_continuity.py` against its draft.
A dead, departed, or missing character appearing again is an error unless the
chapter task explicitly plans the return and the check is run with
`--allow-return <character-id>`. Record the accepted chapter with
`scripts/record_progress.py`; this updates the latest progress and appearance
history so later retrieval sees current state first. A returning character must
also be recorded with `--return <character-id>=<reason>`; the reason becomes
part of chapter history and the character status changes back to `active`.

## Stage gates

1. **Specification gate:** `spec.md` has no unresolved required fields.
2. **Design gate:** core canon and the outline are approved.
3. **Task gate:** the next chapter has a goal, viewpoint, required beats,
   continuity constraints, and exit state.
4. **Draft gate:** retrieval was run for that chapter task.
5. **Acceptance gate:** consistency review passed and the summary, canon, and
   setup statuses were updated.
