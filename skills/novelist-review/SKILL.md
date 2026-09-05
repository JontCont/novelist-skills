---
name: novelist-review
description: "Review, converge, accept, and record one drafted novel chapter into canonical progress. Use only when explicitly invoked as a slash command."
argument-hint: "<novel-project-path> <chapter-number>"
user-invocable: true
disable-model-invocation: true
---

# Review Chapter

Review exactly one draft and update canonical state only after user acceptance.
When `.novelist/config.json` contains the `novelist-sdd` `skill_context` v1
marker, this file is the complete stage reminder: do not load another Novelist
Skill or shared reference unless a failed CLI check names one as necessary.

1. Re-run the SDD gate, structural validation, and character continuity check.
2. Compare prose against the approved task and retrieved evidence. Check
   character state and knowledge, world rules, timeline, setups, viewpoint,
   tense, required beats, exit state, and newly introduced facts.
3. Report gaps without silently changing upstream intent. Fix rejected prose in
   the draft; fix specification defects in their owning artifacts, then repeat
   invalidated approvals, analysis, retrieval, and drafting gates.
4. Present the converged draft to the user. Do not accept it implicitly.
5. After explicit acceptance, write the chapter summary, update confirmed canon
   and setup statuses, then run
   [record_progress.py](../../shared/novelist/scripts/record_progress.py).
6. Stop and instruct the user to run `novelist-chapter` for the next chapter,
   or report that the planned story is complete.
