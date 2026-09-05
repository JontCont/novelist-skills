---
name: novelist-chapter
description: "Specify, analyze, approve, and retrieve context for one novel chapter without drafting prose. Use only when explicitly invoked as a slash command."
argument-hint: "<novel-project-path> <chapter-number>"
user-invocable: true
disable-model-invocation: true
---

# Prepare Chapter

Prepare exactly one chapter. Do not write or modify chapter prose.
When `.novelist/config.json` contains the `novelist-sdd` `skill_context` v1
marker, this file is the complete stage reminder: do not load another Novelist
Skill or shared reference unless a failed CLI check names one as necessary.

1. Verify all plan artifacts have current approvals.
2. Create `chapters/tasks/<NN>.md` from the chapter-task template. Include
   viewpoint, time and location, outline reference, goal, opposition, emotional
   movement, dependency-ordered beats, continuity constraints, setup IDs, exit
   state, and a focused retrieval query.
3. Obtain explicit user approval and record the task approval with
   [sdd.py](../../shared/novelist/scripts/sdd.py).
4. Run the read-only `sdd.py analyze` command. If it fails, repair the owning
   upstream artifact, reapprove invalidated artifacts, and analyze again.
5. Run [retrieve.py](../../shared/novelist/scripts/retrieve.py) with the task's
   query and `--receipt chapters/tasks/<NN>.md`.
6. Run `sdd.py gate`. Stop unless it passes.
7. Stop and instruct the user to run
   `/novelist-skills:novelist-write <project> <chapter-number>`.
