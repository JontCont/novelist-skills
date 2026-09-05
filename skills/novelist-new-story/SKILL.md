---
name: novelist-new-story
description: "Initialize a new specification-driven novel project and establish its binding creative constitution. Use only when explicitly invoked as a slash command."
argument-hint: "<story-slug> <title> [zh-Hant|zh-Hans|ja|en]"
user-invocable: true
disable-model-invocation: true
---

# New Story

Perform only project initialization and constitution ratification. Do not write
the story specification, outline, chapter task, or prose in this command.
Do not load another Novelist Skill or any shared reference. This command creates
the `skill_context` v1 marker used by later reminder-only commands.

1. Require a kebab-case story slug, title, and content locale. Ask only for
   missing values. Supported locales are `zh-Hant`, `zh-Hans`, `ja`, and `en`;
   default to `zh-Hant` only when the user accepts that default.
2. Run [init_novel.py](../../shared/novelist/scripts/init_novel.py) with
   `--locale` from the user's workspace root. It creates `novels/<slug>/`, all
   durable state, and `.novelist/config.json`.
3. Present `constitution.md` to the user. Discuss and edit binding creative
   principles until the user explicitly approves them.
4. Run [sdd.py](../../shared/novelist/scripts/sdd.py) `approve` for
   `constitution.md` only after that approval.
5. Stop. Report the project path and instruct the user to run
   `/novelist-skills:novelist-rule <project>` next.

Never approve the constitution implicitly. Never mark reviewer checklists.
