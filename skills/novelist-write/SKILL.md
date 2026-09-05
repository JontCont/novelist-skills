---
name: novelist-write
description: "Draft or revise one prepared novel chapter after strict SDD and RAG gates pass. Use only when explicitly invoked as a slash command."
argument-hint: "<novel-project-path> <chapter-number>"
user-invocable: true
disable-model-invocation: true
---

# Write Chapter

Write or revise exactly one chapter. Do not approve or record it as accepted.
When `.novelist/config.json` contains the `novelist-sdd` `skill_context` v1
marker, this file is the complete stage reminder: do not load another Novelist
Skill or shared reference unless a failed CLI check names one as necessary.

1. Run [sdd.py](../../shared/novelist/scripts/sdd.py) `gate` for the matching
   chapter task. Stop on any error; never bypass stale approval or RAG receipt.
2. Read only the approved task and receipt sources needed for the scene.
3. Draft `chapters/drafts/<NN>.md`, implementing every required beat and exit
   state without introducing an unplanned major turn.
4. Run [check_continuity.py](../../shared/novelist/scripts/check_continuity.py).
   A non-active character may return only when the task explicitly plans it and
   the user approves `--allow-return`.
5. Stop and instruct the user to review the draft with
   `/novelist-skills:novelist-review <project> <chapter-number>`.

The Plugin `PreToolUse` hook independently enforces the same drafting gate.
