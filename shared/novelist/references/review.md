# Chapter Review

Review the chapter against retrieved evidence before accepting it.

## Checks

- The chapter fulfills the approved task without adding an unapproved major
  turn.
- Character knowledge, motivation, voice, injuries, possessions, and
  relationships match canon and prior summaries.
- Every named character is registered. Characters marked `dead`, `departed`, or
  `missing` do not appear without an approved return beat and explanation.
- Time, travel, location, technology, magic, and social rules remain valid.
- Setups and clues are neither forgotten nor paid off prematurely.
- Point of view and tense match `spec.md`.
- The ending changes the story state and creates a concrete next pressure.
- New proper nouns and facts are either intentional canon additions or removed.

## Acceptance output

After approval:

1. Write a concise chapter summary containing events and state changes.
2. Update affected canon files with confirmed facts only.
3. Update setup statuses: `planned`, `planted`, `advanced`, `paid-off`, or
   `abandoned` with user approval.
4. Advance `state.json.current_chapter` and set the stage for the next task.
5. Use `record_progress.py` to synchronize `story.json`, `progress.json`, and
  each participating character's last appearance.
