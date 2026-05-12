# Math-Classifier Prompt

**Version**: 1.0.0
**Used by**: `src/llmxive/librarian/math_classifier.py` (`classify(...)`), itself called from `LibrarianAgent.invoke()` via the `_maybe_math_question(...)` helper in `src/llmxive/agents/librarian.py`.
**Default backend**: dartmouth (fallback huggingface, then local) — same plumbing the query-extractor uses.

## Purpose

Decide, for one research question, whether it is a **pure-mathematics theorem / proof / formal-structure question** — the kind for which [TheoremSearch](https://theoremsearch.com) (a semantic search engine over theorem *statements*) is a useful third candidate source alongside Semantic Scholar and arXiv.

This classifier is consulted **only** for projects whose field is NOT in `{mathematics, statistics}` (those two fields query TheoremSearch unconditionally — the classifier is skipped). For every other field a single LLM call decides whether the question happens to be a math-theory question that would still benefit from theorem-statement search (e.g. a "physics" project asking for a sharp concentration inequality, or a "computer science" project asking for a worst-case bound on an algorithm).

## Inputs (substituted into the user message)

- `{{question}}` — the research question / search term being investigated.
- `{{idea_body_excerpt}}` — an excerpt of the project idea body for extra context (may be empty / `(none provided)`).

## Output contract

**Reply with `YES` or `NO` on the FIRST line — nothing else on that line.** Then, on a second line, a single short sentence (≤25 words) explaining the verdict. No preamble, no markdown, no extra lines.

- `YES` ⇔ the question is fundamentally about a mathematical theorem, proof, lemma, bound/inequality, exact identity, structural classification, existence/uniqueness result, or other formal mathematical object — i.e. answerable by pointing at a theorem and the paper that proves it.
- `NO` ⇔ the question is primarily empirical, computational, engineering, data-driven, modeling, simulation, survey, software, or otherwise NOT a theorem-shaped question — even if it uses mathematical machinery.

## Guidance

Answer **YES** when the question is, at its core, "what theorem / bound / exact result establishes X, and where is it proved?". Examples that should be **YES**:

- "What is the tightest known concentration inequality for sums of bounded independent random variables, and in which paper is it proved?"
- "Is there a known sharp lower bound on the spectral gap of random d-regular graphs?"
- "What is the current best upper bound on the chromatic number of the plane?"
- "Which paper proves the classification of finite simple groups of a given order type?"
- "What is the optimal constant in the Sobolev embedding W^{1,p} ↪ L^{p*}?"

Answer **NO** when the question is empirical / applied / computational, even if mathematics is involved. Examples that should be **NO**:

- "How does code-clone density correlate with LLM perplexity on Python?"
- "Does data scaling improve calibration of vision transformers in practice?"
- "What is the measured runtime of algorithm X on dataset Y?"
- "How does sensory deprivation change resting-state fMRI modularity?"
- "Which hyperparameters maximize accuracy on benchmark Z?"

Edge cases:

- A question that asks for an *empirical* estimate of a quantity that *also* has a theoretical characterization is **NO** unless the question is explicitly after the theorem (e.g. "estimate the constant in practice" → NO; "what is the proven optimal constant" → YES).
- "Statistics"-flavored questions only reach this classifier when the project field is something else; treat a genuinely theorem-shaped statistics question (a concentration bound, a minimax rate, an asymptotic normality result with proof) as **YES**.
- When in genuine doubt, answer **NO** (the librarian still searches Semantic Scholar + arXiv; a missing TheoremSearch query is a recall loss, not a correctness problem — and a wrong YES wastes an API round-trip but the verification chain still filters the results).
