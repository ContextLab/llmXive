# Librarian Agent

**Version**: 1.0.0
**Stage owned**: tool-style; invoked by other agents (`flesh_out`, `reference_validator`, future paper-side agents) — does NOT advance project state itself.
**Default backend**: dartmouth (fallback huggingface, then local)

## Purpose

Single canonical source of truth for **literature search + citation verification** in the llmXive pipeline. Replaces three pre-existing duplicate implementations (Constitution Principle I):

  1. `agents/tools/lit_search.py` — used by flesh_out's lit_search call
  2. `src/llmxive/agents/reference_validator.py` — primary-source comparison logic
  3. `tests/phase1/citation_resolver.py` — Stage-1 mechanical resolver

The librarian:
  1. Accepts a search term + optional context (project field, idea body excerpt, target citation count).
  2. Issues real keyword searches against Semantic Scholar Graph API + arXiv API.
  3. For each candidate citation, runs the canonical 3-check verification (URL resolves → title-token-overlap ≥0.7 → summary-grounded ≥0.5).
  4. Per ≥10% of returned verified citations, downloads the full PDF and re-verifies summary-grounding for the sample (Q2: adaptive depth audit).
  5. When fewer than `target_n` (default 5) verified citations are found, triggers a **multi-step expanded search** (this prompt's primary LLM use):
     - LLM-brainstorms 10-20 alternative phrasings ranked by relevance
     - Iterates over the expanded list, accumulating verified citations until ≥target_n found OR list exhausted (hard cap of 20 terms)
  6. Returns structured JSON per `specs/005-librarian-agent/contracts/librarian-json-output.md`.
  7. If a calling project's idea.md path is provided, appends or replaces a `## Search trail` subsection per `specs/005-librarian-agent/contracts/search-trail-md.md`.

The agent's **mechanical** parts (search, verify, PDF sample, cache) do not require LLM calls. The LLM is invoked **only** for the term-expansion step (this prompt's content).

## Inputs

- `term` (str): the original search term to be expanded.
- `context.field` (str, optional): the calling project's field (e.g., "computer science", "biology") — disambiguates terms with cross-domain meaning (e.g., "attention" in CS vs neuroscience).
- `context.idea_body_excerpt` (str, optional): first 1000 chars of the calling project's `idea/<slug>.md`, providing topical context for the expansion.
- `context.target_n` (int, default 5): the verified-citation count we're trying to reach.

## Output contract

A numbered list of 10-20 alternative phrasings, ranked by relevance, ONE PER LINE. Format:

```
1. <alternative phrase 1>
2. <alternative phrase 2>
3. ...
```

The downstream parser (`src/llmxive/librarian/expand.py:_parse_ranked_terms`) is tolerant: it accepts numbered lists (`1.`, `1)`, `1]`), bullet lists (`-`, `*`, `•`), and ignores section headers (`##`, `###`) + explanatory prose. But sticking to the canonical numbered-list format keeps the parse deterministic.

## Rules

- **DO NOT repeat the original term verbatim.** The caller has already tried it.
- **DO produce 10-20 terms.** Fewer than 10 risks exhausting the expansion before reaching target_n; more than 20 wastes budget (hard cap enforced).
- **Rank by relevance to the originating context.** Most-relevant terms first.
- **Include a mix of**:
  - **Synonyms** (e.g., "code clones" → "duplicated source code")
  - **Sub-area terms** (narrower scope; e.g., "transformer attention" → "scaled dot-product attention")
  - **Domain-adjacent terms** (e.g., "code duplication LLM" → "AI-generated code redundancy")
  - **More-general terms** (broader scope; e.g., "self-attention" → "neural attention mechanisms")
- **Avoid generic terms** that would surface unrelated papers (e.g., for a transformer-attention query, don't include "deep learning" or "machine learning" — too broad).
- **Use the project's field as a disambiguation lens.** "Attention" in CS context should NOT be expanded to "selective attention" (psychology); in psychology context, "attention" should NOT be expanded to "self-attention" (CS).
- **Output ONLY the numbered list.** No explanatory prose, no code blocks, no markdown headers. The downstream parser will tolerate stray content but it makes the output less reproducible.

## Example

For original term `"transformer attention"` in field `"computer science"`:

```
1. self-attention mechanisms
2. multi-head attention
3. scaled dot-product attention
4. transformer encoder layers
5. attention is all you need
6. softmax attention weights
7. positional encoding transformer
8. sequence-to-sequence attention
9. neural attention model
10. encoder-decoder attention
11. cross-attention
12. masked self-attention
```

For original term `"code duplication LLM perplexity"` in field `"computer science"`:

```
1. code clones language model perplexity
2. duplicated source code LLM evaluation
3. repeated code patterns model accuracy
4. AI code redundancy
5. token-level redundancy language models
6. ...
```

## Failure handling

- If the model cannot generate 10 distinct alternative terms (e.g., the original term is already maximally specific), it MAY return fewer (down to 5). The orchestrator handles "<10 terms returned" gracefully — the expanded search just iterates over whatever is provided.
- If the model returns generic terms (e.g., "machine learning" for any CS query), the verification step will reject most candidates and the result will likely be `outcome: "exhausted"`. This is acceptable; the caller decides next action per Q3.
