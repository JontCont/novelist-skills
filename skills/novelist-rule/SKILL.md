---
name: novelist-rule
description: "Complete and approve the story specification for an initialized novel project. Use only when explicitly invoked as a slash command."
argument-hint: "<novel-project-path>"
user-invocable: true
disable-model-invocation: true
---

# Story Rules

Perform only specification and clarification. Do not create canon, an outline,
a chapter task, or prose in this command.
When `.novelist/config.json` contains the `novelist-sdd` `skill_context` v1
marker, this file is the complete stage reminder: do not load another Novelist
Skill or shared reference unless a failed CLI check names one as necessary.

1. Run [sdd.py](../../shared/novelist/scripts/sdd.py) `check` for
   `constitution.md`. Stop if its approval is missing or stale.
2. Read `.novelist/config.json`, then interview for genre, target length,
   audience, language variety and orthography, tone, viewpoint and tense,
   premise, protagonist, desire, obstacle, stakes, boundaries, and ending.
3. Write decisions to `spec.md`. Use `[NEEDS CLARIFICATION: question]` for any
   choice that has no safe default, then resolve every marker with the user.
4. Present `checklists/requirements.md` to the user. The user is the reviewer;
   the agent must not check boxes on the user's behalf.
5. After the reviewer completes the checklist and explicitly approves the
   specification, run `sdd.py approve <project> spec.md`.
6. Stop and instruct the user to run `/novelist-skills:novelist-plan <project>`.
