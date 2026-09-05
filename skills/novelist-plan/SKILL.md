---
name: novelist-plan
description: "Create and approve novel canon, structured characters, timeline, setups, and outline. Use only when explicitly invoked as a slash command."
argument-hint: "<novel-project-path>"
user-invocable: true
disable-model-invocation: true
---

# Plan Novel

Perform only canon and outline planning. Do not create a chapter task or prose.
When `.novelist/config.json` contains the `novelist-sdd` `skill_context` v1
marker, this file is the complete stage reminder: do not load another Novelist
Skill or shared reference unless a failed CLI check names one as necessary.

1. Run [sdd.py](../../shared/novelist/scripts/sdd.py) `check` for
   `constitution.md` and `spec.md`. Stop if either approval is missing or stale.
2. Complete `characters.json`, including stable IDs, personality, lifecycle
   status, location, and protagonist references in `story.json`.
3. Complete world, character, timeline, and setup canon files.
4. Run project validation and resolve every structural error.
5. Ask the user to approve each canon artifact, then approve them in dependency
   order with [sdd.py](../../shared/novelist/scripts/sdd.py).
6. Build `outline/outline.md` from approved spec and canon. Complete its
   Constitution Check and obtain explicit user approval before recording it.
7. Stop and instruct the user to run
   `/novelist-skills:novelist-chapter <project> <chapter-number>`.
