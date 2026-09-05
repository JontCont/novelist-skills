# Strict SDD Workflow

This workflow adapts the full GitHub Spec Kit sequence rather than only its
short specify-plan-tasks-implement path. The novel-specific mapping preserves
constitution authority, reviewer-owned checklists, read-only analysis, ordered
tasks, and convergence while adding canon and RAG controls.

Novel artifacts form an ordered dependency graph. An artifact is approved by
recording its SHA-256 digest in `.novelist/approvals.json`. Editing it afterward
makes the approval stale; never copy approval hashes manually.

## Gates

1. **Constitute:** ratify binding creative and governance principles.
2. **Discover:** interview the user and resolve every required field in
   `spec.md`.
3. **Clarify:** remove every `[NEEDS CLARIFICATION]` marker, then have the
   reviewer complete every specification-quality checklist item.
4. **Specify:** user approves `spec.md`.
5. **Model canon / plan:** complete and approve `characters.json` and every required
   file under `canon/`.
6. **Outline / plan:** approve `outline/outline.md` only after its dependencies are
   current.
7. **Tasks:** create and approve `chapters/tasks/<chapter>.md`, including an
   outline reference and dependency-ordered required beats.
8. **Analyze:** run read-only cross-artifact consistency analysis.
9. **Retrieve:** run a focused query with `retrieve.py --receipt` for that task.
   The receipt binds the query, sources, task hash, and knowledge-corpus hash.
10. **Implement / draft:** run `sdd.py gate`; only a passing gate permits writing the
   matching file under `chapters/drafts/`.
11. **Converge:** run structural and continuity checks, compare prose against
    constitution/spec/outline/task, append required fixes, obtain user
    acceptance, and record progress only when no gap remains.

## Commands

```powershell
python shared/novelist/scripts/sdd.py approve <project> constitution.md
python shared/novelist/scripts/sdd.py approve <project> spec.md
python shared/novelist/scripts/sdd.py approve <project> characters.json
python shared/novelist/scripts/sdd.py approve <project> canon/world.md
python shared/novelist/scripts/sdd.py approve <project> canon/characters.md
python shared/novelist/scripts/sdd.py approve <project> canon/timeline.md
python shared/novelist/scripts/sdd.py approve <project> canon/setups.md
python shared/novelist/scripts/sdd.py approve <project> outline/outline.md
python shared/novelist/scripts/sdd.py approve <project> chapters/tasks/01.md
python shared/novelist/scripts/retrieve.py <project> "第一章人物與場景約束" --receipt chapters/tasks/01.md
python shared/novelist/scripts/sdd.py analyze <project> --task chapters/tasks/01.md
python shared/novelist/scripts/sdd.py gate <project> --task chapters/tasks/01.md
```

## Invalidation rules

- Changed artifact hash: its own approval is stale.
- Changed canon, outline, progress, research, summary, or task: prior RAG
  receipts are stale because the corpus digest changes.
- Changed chapter task: its approval and receipt are both stale.
- Failed gate: do not draft, revise the failed upstream artifact, reapprove it,
  rerun retrieval, and gate again.
- User acceptance is mandatory. An agent must not approve an artifact merely
  because it generated it.

The Copilot plugin hook enforces the drafting gate before write tools execute.
Hooks are a deterministic backstop; the workflow remains mandatory on clients
that do not implement Copilot hooks.
