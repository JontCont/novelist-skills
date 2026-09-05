# Retrieval

Retrieval supplies only the most relevant story knowledge to the current task.
It does not decide canon and must not copy every project file into context.

## Before each operation

Build a focused query from the operation:

- Planning: viewpoint character, locations, active arcs, unresolved setups.
- Drafting: chapter task, participating characters, recent summaries, world
  rules used in the scene, and promised payoffs.
- Revising: the reported issue plus affected characters, facts, and chapters.
- Continuity review: every concrete claim that may conflict with prior canon.

Run:

```powershell
python shared/novelist/scripts/retrieve.py <project> "<query>" --top 8
```

Use `--json` when structured output is more useful. For each decision, retain
the returned source path and line number. If results are weak, reformulate the
query with names and concrete facts; do not compensate by inventing context.

## Corpus boundaries

The retriever searches specification, canon, outline, chapter tasks, accepted
chapter summaries, and research notes. It intentionally excludes chapter
drafts because unaccepted prose is not authoritative.

`story.json`, `characters.json`, and `progress.json` receive the highest ranking
boost. Every drafting query should include the chapter number and participating
character names so personality, lifecycle status, last appearance, location,
and latest progress are retrieved together.

The current implementation is lexical retrieval with Chinese character
bigrams and Latin word tokens. Its interface is intentionally stable so a
vector or hybrid retriever can replace it later.

## Locale configuration

`.novelist/config.json` controls retrieval normalization and tokenization.
Supported content locales are `zh-Hant`, `zh-Hans`, `ja`, and `en`. CJK
locales default to character bigrams; English defaults to word tokens. Unicode
NFKC normalization makes full-width and compatibility forms comparable.

Use `retrieval.term_aliases` for project vocabulary, historical spellings, and
Traditional/Simplified variants that must resolve to the same concept:

```json
{
  "term_aliases": {
    "玉佩": ["玉珮"],
    "計畫": ["計劃"]
  }
}
```

Aliases are applied to both indexed chunks and queries. Keep this list focused;
ambiguous aliases reduce precision. `retrieval.stopwords` can remove recurring
function words or template terms that dominate results without carrying story
meaning. Changing locale or retrieval settings invalidates existing receipts.
