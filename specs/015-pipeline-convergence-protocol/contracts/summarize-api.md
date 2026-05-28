# Contract — `summarize` / `desummarize` (`src/llmxive/tools/summarize.py`)

SSoT context-reduction primitive. Implements spec FR-001…008. Generalizes the single-pass `paper_reviewer._build_corpus_with_summaries`; that function is re-pointed to call this (no fork).

## API

```python
def summarize(
    content: str,
    *,
    goal: str,                      # PRESERVATION CONTRACT (see goals below)
    model: str,                     # e.g. "qwen.qwen3.5-122b"
    token_budget: int | None = None,  # default resolved from model (qwen→32768) minus completion headroom
    cache_dir: str | Path | None = None,
) -> str:
    """Return `content` verbatim if it fits the budget; otherwise return a compact,
    model-readable POINTER BLOCK naming an on-disk manifest + the verbatim critical
    elements that fit. Never silently drops a check-critical element."""

def desummarize(
    text: str,
    *,
    want: list[str] | None = None,  # optional element-ids / patterns to page in (else all)
    max_depth: int = 16,
) -> str:
    """Recursively resolve a pointer block produced by summarize() back into the
    underlying content (or just the requested `want` elements). Every pointer MUST
    resolve to a real on-disk file (no dangling references)."""
```

## Goals (preservation contracts)
The `goal` string declares what MUST survive verbatim. Recognized goal families (extensible):
- `"preserve every URL/DOI/arXiv-id verbatim"` — link-reachability checks.
- `"preserve the full argument chain"` — logic/consistency checks.
- `"preserve all numeric results/claims verbatim"` — claim-accuracy.
- `"preserve every FR/SC/task id"` — coverage checks.

## Behavior (FR-002…007)
1. **Fit check** — `estimate_tokens(content) ≤ token_budget` → return verbatim.
2. **Extraction (deterministic, no LLM)** — collect the goal's check-critical elements via regex/parse (URLs, DOIs, arXiv ids, citation keys, FR/SC/task ids, numbers). These are preserved verbatim at every level.
3. **Boundary-aware chunking** — never split an atomic unit (URL/DOI/id/equation/code block/table row/figure ref) mid-token; chunk at LaTeX/markdown/paragraph boundaries (reuse `_chunk_corpus`).
4. **Goal-targeted per-chunk summary (LLM)** — only for semantic prose; reuse the cached `_summarize_chunk` call; carry the chunk's critical elements verbatim.
5. **Recurse** — if the joined manifest still overflows, a chunk entry becomes a `pointer` to a nested manifest. Critical elements re-injected at each level (no recursion loss).
6. **On-disk inode-table** — `<cache_dir>/<sha256[:16]>/manifest.json` + content files (see data-model `SummaryManifest`/`SummaryEntry`).
7. **No silent truncation** — when extracted criticals alone exceed budget, build a deeper pointer hierarchy keeping every critical reachable on disk; NEVER drop one.

## Invariants (tested)
- `set(all critical across all manifest levels) == set(extracted criticals from source)` — zero loss.
- `desummarize(summarize(x, goal=g)) ` recovers every check-critical element for goal `g`, in order, none cut mid-token.
- A reviewer's critical verdicts on `summarize(x)` == its verdicts on `x` (SC-002).
- Every pointer resolves to an existing file (FR-007).

## Edge cases (each a real-example regression test, FR-004)
atomic-unit splitting · cross-chunk references · cross-chunk logic · quantitative claims · ordering-sensitive content · output cut-off (summary hits completion budget → detect+continue) · recursion-loss compounding.

## Callers (FR-006)
`paper_reviewer` (re-pointed), `planner`, `tasker`/analyze, `specifier`, `clarifier`, `paper_specifier`, `paper_clarifier`, `paper_planner`, `paper_tasker`, the convergence engine (any overflowing reviewer/reviser input), and triage (large reviews). Each MUST also support `desummarize` to page content in on demand.
