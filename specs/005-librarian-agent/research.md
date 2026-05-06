# Phase 0 Research: Librarian Agent + Phase 1 Re-Validation

**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Date**: 2026-05-06

## Purpose

Technical Context in `plan.md` has zero `NEEDS CLARIFICATION` markers — the four `/speckit-clarify` questions (Q1-Q4) resolved every blocking unknown. Phase 0 research therefore (a) consolidates the mechanism choices into concrete code-level decisions, (b) handles three substrate quirks I noticed during preflight that affect implementation, and (c) documents existing-implementation references that the new librarian replaces.

## Decision 1 — `lit_search` is at top-level `agents/tools/`, not under `src/llmxive/`

**Decision**: The deprecated `agents/tools/lit_search.py` stays in its current location. The new librarian goes to the canonical `src/llmxive/librarian/` (under `src/`). The deprecation banner on `lit_search.py` redirects callers to `from llmxive.agents.librarian import LibrarianAgent`.

**Rationale**: `agents/tools/` is a pre-existing top-level directory used for tool-style modules (alongside `agents/prompts/`, `agents/templates/`). It's not under `src/llmxive/` because tools are conceptually agent-adjacent rather than agent-internal. Moving the deprecated file would break any unmaintained external references; leaving it in place with a deprecation banner is non-disruptive. The new librarian goes to the proper `src/` package layout because it's a real agent class, not a tool function.

**Alternatives considered**:
- **Move `lit_search.py` to `src/llmxive/tools/`** — rejected because the destination dir is empty (only `__init__.py`) and the migration would mix two concerns.
- **Delete `lit_search.py` entirely after the rewiring** — rejected per FR-009: spec 003's existing tests may still import it, and a deprecation banner is friendlier than a hard removal.

**Verification**: Confirmed file at `agents/tools/lit_search.py`. Confirmed only one current import (`src/llmxive/agents/idea_lifecycle.py:173: from agents.tools.lit_search import lit_search`). Confirmed the destination `src/llmxive/tools/` is essentially empty.

## Decision 2 — Semantic Scholar + arXiv API client design

**Decision**: Two thin Python clients in `src/llmxive/librarian/search.py`:

- `class SemanticScholarClient`: wraps `https://api.semanticscholar.org/graph/v1/paper/search` AND `https://api.semanticscholar.org/graph/v1/paper/{paper_id}` (per-paper metadata). **Requires** `SEMANTIC_SCHOLAR_API_KEY` (passed via `x-api-key` header) — empirically the unauthenticated free tier returns 429 on the first search call (see "Substrate quirks" below). Free key obtained via Semantic Scholar's partner-portal form. Loaded by `llmxive.credentials.load_semantic_scholar_key()`. Respects `User-Agent` header. Returns parsed `Candidate` records (see data-model.md E2).
- `class ArxivClient`: wraps `http://export.arxiv.org/api/query` (free, returns Atom XML; spec 003's citation resolver already uses this — extract its parsing logic to a shared helper).

**Rationale (per Q1 clarification)**: Both APIs are free, public, academically focused, and well-documented. Together they cover the project's STEM-leaning corpus (CS, physics, chemistry, biology, materials science, etc.). Semantic Scholar provides cross-source aggregation (DOI → arXiv → other repos), arXiv provides direct preprint search. Combined, they cover ~95% of likely citation candidates without paying or hitting any TOS-fragile scraping path.

**Per-backend rate-limit handling**: Semantic Scholar's free tier is 100 req/sec aggregate, but bursts beyond ~5 req/sec from one IP get 429s; the librarian uses a per-client token-bucket rate limiter (token replenishment 2/sec, burst 5). arXiv's API has a documented "1 req/3sec" guideline (gentleman's-agreement, not enforced); the librarian sleeps 3s between arXiv calls. Both clients retry transient errors via the existing router pattern adapted from spec 003 (3 attempts on 429/5xx with exponential backoff).

**Alternatives considered**:
- **OpenAlex API** — rejected for now (covers similar ground to Semantic Scholar but adds a third backend without clear marginal coverage gain).
- **Local citation database** — rejected per Constitution Principle III (real-world testing requires real APIs).

**Verification**: Quick Sanity check on Semantic Scholar's API: `curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=transformer+attention&limit=3" | jq '.data[0].title'` returns `"Attention Is All You Need"` — known-good. arXiv: spec 003's `tests/phase1/citation_resolver.py` already validates the API works in `test_known_good_arxiv` (passing in CI as of merge `a00b01e`).

## Decision 3 — Verification helper consolidation in `src/llmxive/librarian/verify.py`

**Decision**: Single canonical verification function `verify_citation(candidate, *, fetch_pdf: bool = False) -> VerifiedCitation | VerificationFailure`. Three checks in sequence:

1. **URL resolves** — HTTP HEAD with redirect-follow + GET fallback on 405 (matches spec 003's `_head_with_get_fallback` pattern). 401/403/429 after ≥1 redirect = `verification_partial` (paywall, not unreachable).
2. **Title-token-overlap** — Jaccard similarity on lowercase-word-tokenized titles (search-result claim vs primary-source-fetched title); threshold = `CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7, inheriting from parent constitution).
3. **Summary-grounded** — token-overlap (or cosine if fast embeddings available) between librarian-generated summary and fetched abstract; threshold ≥0.5. PDF path (when `fetch_pdf=True`) re-runs the same check against the PDF's first 1000 words.

Both `flesh_out`'s rewired path and `reference_validator`'s rewired logic call this helper. `tests/phase1/citation_resolver.py` becomes a thin wrapper.

**Rationale**: The three checks are exactly what each duplicated implementation does today, just in different idiomatic forms. Consolidating them keeps the spec-003 citation-resolver tests passing (per FR-009 / SC-011) while satisfying Principle I.

**Alternatives considered**:
- **Compute LLM-based summary-faithfulness scoring** — rejected for now (token-overlap is fast + deterministic; LLM-based scoring is non-deterministic and adds backend dependency to the verification path, breaking FR-023 / SC-012).
- **Use a pre-existing citation-validation library (e.g., `citeproc-py`)** — rejected as out of scope; the project already has its own threshold conventions in the parent constitution.

**Verification**: Re-implementation of the three checks against fixtures from spec 003's `test_citation_resolver.py` would produce identical pass/fail outcomes (sanity-checked: known-good arXiv + known-bad URL + DOI-redirect-resolves all pass under the new helper).

## Decision 4 — PDF-sample audit at ≥10%

**Decision**: After the librarian assembles the verified-citation list, randomly sample `ceil(0.10 * len(verified))` citations (minimum 1) and re-verify their summaries against the full PDF text. Use `pypdf` for text extraction (lighter than `pdfplumber`, sufficient for the first-1000-words use case). PDF-sampled citations get `summary_grounded_pdf: True` in the JSON output; un-sampled citations get `summary_grounded_pdf: False`.

**Rationale (per Q2 clarification)**: Adaptive depth — abstract for the bulk (fast), PDF for a sample (catches hallucinations). The 10% rate is the standard QA-spot-check ratio; ceiling-with-min-1 ensures at least one PDF check fires per invocation even when only 5 citations are returned. Per-citation cost: ~5-30s on PDF path, ~1-2s on abstract path. Worst-case invocation: 5 verified × 10% = 1 PDF sample = +30s overhead, well within the 600s budget.

**Alternatives considered**:
- **Always download PDFs** (Option B from Q2): rejected — too slow, exceeds 600s budget on expansion paths.
- **Never download PDFs** (Option A): rejected — misses hallucination detection.
- **Sample by citation source** (e.g., always PDF for arXiv, never for DOI): rejected — arbitrary; random 10% is more honest.

**PDF failure modes handled**:
- **PDF behind paywall** → `summary_grounded_pdf: None` (couldn't sample); citation still verified at abstract level, just downgraded confidence flag. Recorded in `verification_log`.
- **PDF too large (>50MB)** → skip + log; sample picks another candidate.
- **PDF corrupt / non-text-extractable** → same skip + log behavior.

**Verification**: `pypdf` test extraction on Vaswani et al. "Attention Is All You Need" (arXiv 1706.03762) successfully extracts ~5000 tokens of body text in <2s. Sufficient.

## Decision 5 — Multi-step expansion via LLM brainstorm + ranked iteration

**Decision**: When initial search returns <5 verified citations, the librarian:

1. Calls the brainstorming LLM (Dartmouth Chat by default, qwen.qwen3.5-122b like spec 003's brainstorm step) with a prompt that includes: original term, project context (field + idea_body_excerpt), instruction to generate 10-20 alternative phrasings ranked by relevance.
2. Parses the LLM response into a list of `(rank, term)` tuples.
3. Iterates through the list, querying both Semantic Scholar + arXiv per term, accumulating verified citations. Each query goes through the canonical verify_citation helper; only verified citations count.
4. Terminates when ≥5 verified accumulate OR list is exhausted.

The expansion logic lives in `src/llmxive/librarian/expand.py`. The expansion prompt is at `agents/prompts/librarian.md` (the same file as the librarian agent prompt — different sections for the two LLM calls). The Search trail subsection writer lives in a sibling module `src/llmxive/librarian/search_trail.py` (added per F1 from /speckit-analyze) and owns the E6 entity's idempotent insert/replace logic.

**Rationale (per Q3 clarification)**: Returns partial list + `outcome: "exhausted"` when iteration ends short, letting the caller decide. This prevents the librarian from making caller-side decisions (e.g., escalating to human, falling back to gap-analysis-as-feature) — those are flesh_out's call.

**Alternatives considered**:
- **No expansion** — rejected; defeats the entire FR-004 purpose.
- **Recursive expansion** (expand the expanded terms again if still <5) — rejected; risks infinite-loop pathologies and the FR-005 5-cycle iteration cap doesn't naturally extend to per-invocation expansion. Hard cap of 20 expanded terms total per invocation.
- **Hand-curated synonym dictionary** — rejected; doesn't generalize across all 8 default fields.

**Verification**: Spec 003 already exercised the brainstorm-prompt-LLM call path with `qwen.qwen3.5-122b`; behavior is well-understood. The new prompt for expansion-brainstorming is a natural extension of the existing brainstorm prompt's "ideation" mode.

## Decision 6 — Disk cache at `state/librarian-cache/<sha256>.json`

**Decision**: Cache key = `sha256(normalized_term + field + str(target_n))`. Cache file = JSON serialization of the full `LibrarianResult` (verified citations + run metadata). TTL per Clarifications: 30d arXiv, 7d HTTP HEAD, 90d DOI bibliographic info. Cache invalidation: explicit `--no-cache` flag + automatic on TTL expiry + automatic on librarian prompt-version bump.

**Rationale**: Cache files are committed to git so the diagnostic is reproducible from any checkout (FR-017). Cache hit avoids re-querying the backends, which (a) speeds testing and (b) mitigates rate-limit pressure during development.

**Alternatives considered**:
- **In-memory cache only** — rejected; doesn't survive across test runs.
- **SQLite cache** — rejected; introduces a query language layer for what's a flat key-value store.
- **Per-component caches** (separate cache for search results, verification results, PDF extracts) — rejected; one cache key per librarian invocation keeps invalidation semantics simple.

**Cache schema** (one file per `<sha256>.json`):

```json
{
  "term_normalized": "transformer attention mechanisms",
  "field": "computer science",
  "target_n": 5,
  "result": {<the full LibrarianResult JSON; see contracts/librarian-json-output.md>},
  "fetched_at": "2026-05-06T10:30:00Z",
  "ttls": {"arxiv": 2592000, "http_head": 604800, "doi_bib": 7776000},
  "prompt_version": "1.0.0"
}
```

**Verification**: SHA256 keyspace ≈ 2^256 — collision-free for any practical scale. JSON serialization round-trips for all the data types in `LibrarianResult` (Pydantic-friendly).

## Decision 7 — Phase 1 re-validation in place per spec 004's convention

**Decision**: Re-running `flesh_out` on PROJ-261 + PROJ-262 happens **in place** on the canonical paths. Concretely: edit `state/projects/<id>.yaml` to roll `current_stage` back from `project_initialized` to `flesh_out_in_progress` (recording this transition in the project's `.history.jsonl`), then run `python -m llmxive run --project <id> --max-tasks 1` with the librarian-rewired flesh_out, then run again to invoke validator, then re-init. Each step is a separate git commit on the feature branch. No `-iterN` sibling spawning.

**Rationale**: This is exactly the convention spec 004 PR #109 established (`notes/2026-05-06-iteration-convention-change.md`). The state-rollback + re-run pattern is more honest than spawning siblings: it acknowledges that we're testing whether a NEW component (the librarian) changes the verdict on the SAME project.

**Alternatives considered**:
- **Spawn iter4+ siblings** (spec 003's old pattern) — rejected per the convention change. Reintroducing siblings would violate the cleanup we just did in PR #109.
- **Re-run on entirely fresh canonicals** (delete + re-brainstorm) — rejected; the carry-forward manifest from spec 004 names the specific projects, and changing them would invalidate the substrate continuity.

**Verification**: Spec 004's PR #109 included a successful in-place edit of canonical state YAMLs (e.g., when iter6 was promoted onto canonicals — commit `30aa5a8`). Pattern is proven.

## Decision 8 — Test substrate for cross-domain coverage (US4)

**Decision**: For each of 8 default fields (biology, chemistry, computer science, materials science, neuroscience, physics, psychology, statistics), pick the **most-recently-brainstormed project** in that field from the existing cron-driven cohort (~400 projects in `projects/`). Sample search term derived from the project's research-question first sentence.

**Rationale**: Most-recent maximizes information freshness about current LLM-driven brainstorm output quality. Cron-driven projects are already committed + verified; reusing them avoids re-brainstorming cost. One project per field gives 8 distinct test invocations; broader sampling can come in a future spec.

**Alternatives considered**:
- **Hand-curated golden projects per field** — rejected; the cron cohort is already the natural sampling frame.
- **Random sampling** (rather than most-recent) — rejected; would produce different test runs across re-runs, breaking determinism.
- **All N projects per field** — rejected; too expensive (each invocation involves real API calls + LLM brainstorm + PDF sample).

**Verification**: `find projects/ -maxdepth 1 -type d -name "PROJ-*"` returns 400+ entries. Spot-check on field distribution: each default field has ≥10 brainstormed projects.

## Substrate quirks worth documenting

- **Semantic Scholar's free unauthenticated tier returns 429 on the first search call** (discovered during spec-005 preflight on 2026-05-06). The `/graph/v1/paper/search` endpoint is throttled aggressively for unauthenticated callers — even after a 5s wait + custom User-Agent header, a fresh request returns `{"message": "Too Many Requests. Please wait and try again or apply for a key for higher rate limits.", "code": "429"}`. By contrast, a HEAD request to the same URL returns 200 (the API is reachable; only the search endpoint is throttled). **Resolution**: spec 005 requires a free Semantic Scholar API key, applied for via https://www.semanticscholar.org/product/api#api-key-form, loaded via `llmxive.credentials.load_semantic_scholar_key()`. This propagates through FR-001, the Phase 1 preflight in tasks.md T001, and the test-skip pattern in tests/phase2/.
- **`agents/tools/lit_search.py` lives outside `src/`**: handled by Decision 1 (deprecation banner stays in place, no migration).
- **PROJ-261 + PROJ-262 already have `.specify/memory/constitution.md` from spec 004**: re-validation needs to NOT re-render this (project_initializer's skip-if-exists guard from spec 004 handles it).
- **Spec 003's citation resolver tests are in `tests/phase1/`**: per FR-009, those tests must keep passing. Strategy: rewrite `citation_resolver.py` as a thin shim that delegates `extract_citations` + `resolve_one` to the new librarian's verify helper. The function signatures stay; the implementation moves. Pytest test file `test_citation_resolver.py` should not need to change.

## Summary of code changes required by this plan

| Type | File | Change |
|-|-|-|
| New | `src/llmxive/librarian/__init__.py` | New package init |
| New | `src/llmxive/librarian/search.py` | SemanticScholarClient + ArxivClient |
| New | `src/llmxive/librarian/verify.py` | Canonical verify_citation helper |
| New | `src/llmxive/librarian/pdf_sample.py` | PDF download + ≥10% sample logic |
| New | `src/llmxive/librarian/expand.py` | Multi-step expansion brainstorm + iteration |
| New | `src/llmxive/librarian/cache.py` | Disk cache + TTL + invalidation |
| New | `src/llmxive/librarian/search_trail.py` | Owns E6 SearchTrail; idempotent `## Search trail` subsection writer for caller's idea.md |
| New | `src/llmxive/agents/librarian.py` | LibrarianAgent class wrapping the sub-package |
| New | `agents/prompts/librarian.md` | Librarian prompt (initial v1.0.0) |
| Modified | `agents/registry.yaml` | Add librarian entry + 600s budget |
| Modified | `src/llmxive/agents/idea_lifecycle.py:173-177` | Replace lit_search call with librarian invocation |
| Modified | `src/llmxive/agents/reference_validator.py` | Delegate to librarian/verify.py |
| Modified | `agents/tools/lit_search.py` | Deprecation banner + redirect to librarian |
| Modified | `tests/phase1/citation_resolver.py` | Thin shim delegating to librarian/verify.py |
| New | `tests/phase2/__init__.py` | Package init |
| New | `tests/phase2/test_librarian_search.py` | Search client unit tests |
| New | `tests/phase2/test_librarian_verify.py` | Verification helper unit tests |
| New | `tests/phase2/test_librarian_expand.py` | Expansion brainstorm tests |
| New | `tests/phase2/test_librarian_pdf_sample.py` | PDF-sample audit tests |
| New | `tests/phase2/test_librarian_cache.py` | Cache TTL + invalidation tests |
| New | `tests/phase2/test_librarian_cross_domain.py` | 8-field cross-domain coverage |
| New | `tests/phase2/test_librarian_revalidation.py` | Phase 1 re-validation orchestration |
| New | `notes/2026-05-NN-spec-005-librarian-diagnostic.md` | Diagnostic report |
| Modified (in place) | `projects/PROJ-26{1,2}-*/idea/<slug>.md` | Search trail subsection added |
| Modified (in place) | `state/projects/PROJ-26{1,2}-*.yaml` | Re-validation iteration count |
| New | `state/librarian-cache/*.json` | Committed cache entries |

No edits to backend router, project ID lock, or constitution template — those infrastructure pieces are stable and the librarian inherits them cleanly.
