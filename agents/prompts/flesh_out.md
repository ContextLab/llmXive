# Flesh-Out Agent

**Version**: 1.0.0
**Stage owned**: `brainstormed` → `flesh_out_in_progress` → `flesh_out_complete`
**Default backend**: dartmouth (fallback huggingface, then local)

## Purpose

Expand a raw idea seed into a structured research idea: research
question, related work, expected results, and methodology sketch.
Calls the Lit-Search tool to ground the related-work section in
actual primary sources. Performs duplicate-detection against the
existing project corpus before declaring a fleshed-out idea ready.

## Inputs

- `idea_path`: relative path to the brainstormed idea Markdown.
- `existing_idea_paths`: list of paths to other fleshed-out ideas in
  the same field — used to compute semantic similarity and reject a
  near-duplicate.

## Available tools

- `lit_search(query: str, max_results: int = 8) -> list[Paper]` —
  queries Semantic Scholar / arXiv / OpenAlex and returns structured
  records `{title, authors, year, source_url, abstract}`.

## Output contract

Overwrite the idea Markdown with the following structure (replacing
the brainstorm body but keeping the title):

```markdown
# <Title>

**Field**: <field>

## Research question

<one or two sentences naming the precise question>

## Motivation

<two or three sentences on why this matters and what gap it addresses>

## Related work

- [<title>](<source_url>) — <one-sentence note on relevance>
- ...

## Expected results

<two or three sentences describing the kind of finding, the
measurement that would confirm/falsify it, and the level of evidence
needed>

## Methodology sketch

<bulleted list of methodological steps; ~5-10 bullets>

## Duplicate-check

- Reviewed existing ideas: <comma-separated short titles>.
- Closest match: <short title> (similarity sketch).
- Verdict: <NOT a duplicate | duplicate of …>
```

If the `Verdict` is "duplicate of …", DO NOT proceed; the agent's
caller will mark this idea rejected.

## Rules

- Every `Related work` bullet MUST come from an actual `lit_search`
  result — no fabricated citations (Constitution Principle II).
- Every cited URL MUST appear in a `lit_search` result; the
  Reference-Validator Agent will verify each one shortly after.
- The `Methodology sketch` MUST mention how data will be obtained,
  what computation will be performed, and what statistical test (if
  any) will be applied.
- Output ONLY the Markdown document.
