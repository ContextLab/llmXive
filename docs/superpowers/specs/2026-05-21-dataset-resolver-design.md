# Design: Deterministic Dataset Resolver

**Date**: 2026-05-21
**Status**: Approved (design) — pending implementation plan
**Topic**: Web-search-driven, deterministic dataset URL resolution for the Planner

## Context

During spec-014 (Phase-4 validation), the Planner (`qwen.qwen3.5-122b`) repeatedly emitted
**hallucinated/unreachable dataset URLs** in `research.md`, even though the planner prompt
already says "NEVER invent URLs." On PROJ-262 ("predicting molecular dipole moments"), five
consecutive samplings each cited a *different* dead URL (figshare DOI 404, NAB github dir 404/400,
`quantum-machine.org/datasets/qm9.zip` 404, `deepmind.com/.../qm9` 404). FR-006 (URL reachability,
strict hard-fail per the 2026-05-21 decision) correctly rejected all of them — but the project
could not advance because the LLM cannot reliably produce a correct URL.

**Decision (user, 2026-05-21):** dataset URLs must be **identified from web search of real
sources, not hallucinated**, and the process must be **deterministic** (not primarily LLM-driven):
datasets are found from promising sources, then automatically downloaded/tested for proper format
before being used.

## Goal

Remove the "produce a correct dataset URL" task from the LLM. A deterministic resolver finds real,
reachable, format-checked dataset sources and injects the **top-N verified candidates per dataset**
into the Planner's prompt; the Planner only *cites* them. `research.md` becomes correct by
construction and FR-006 passes naturally (and remains the safety net).

### Non-goals
- Full dataset download (that stays the Implementer's job, Phase 5).
- A general web-search engine dependency (keeps the resolver deterministic; out of scope).
- Changing FR-006's strictness (it stays; it just stops firing because URLs are now real).

## Architecture (Approach A)

A resolver **module in the `librarian/` package**, called by the Planner's mechanical step — no new
pipeline stage, maximal reuse of existing search/verify/cache infra.

```
Planner.mechanical_step
   └─ librarian.dataset_resolver.resolve_datasets(spec_text, ...) -> ResolvedDatasets
        ├─ query_extractor      : extract dataset intents from spec.md (deterministic-first)
        ├─ dataset_sources      : HF Hub, figshare, Zenodo, DataCite, (reuse) Semantic Scholar/arXiv
        ├─ verify._head_with_get_fallback : reachability
        ├─ _sniff_format         : sample-stream + parse the claimed format
        └─ cache                : memoize search/verify/sniff
Planner.build_prompt
   └─ inject "Verified datasets — cite ONLY these" block (top-N per intent)
```

## Components (all under `src/llmxive/librarian/`)

- **`dataset_resolver.py`** (new) — orchestrator. `resolve_datasets(spec_text, *, project_dir, repo_root, budget_s=300, top_n=3) -> ResolvedDatasets`.
- **`dataset_sources.py`** (new) — thin, deterministic clients, each returning candidate `(url|hf_id, title, source, metadata)`:
  - HuggingFace Hub via `huggingface_hub` (search datasets, dataset card + file list, stream first rows).
  - figshare REST (`api.figshare.com/v2/articles/search`), Zenodo REST (`zenodo.org/api/records`), DataCite (`api.datacite.org/dois`) — DOI resolution + keyword search.
- **Reused unchanged**: `query_extractor.py` (intent extraction), `search.py` (Semantic Scholar + arXiv → source-paper data links), `verify.py` (`_head_with_get_fallback`), `cache.py`.
- **Format sniff** (`_sniff_format` in `dataset_resolver.py`): stream first N MB (cap, timeout) or HF streaming first rows; detect + parse `csv/tsv/parquet/json(l)/hdf5/zip/tar/xyz/sdf`; return `{format, parsed: bool, downloaded_bytes, error?}`.

## Data flow

1. `Planner.mechanical_step` calls `resolve_datasets(spec_text, ...)`.
2. **Extract dataset intents** from `spec.md`: DOIs via regex; named datasets (e.g. "QM9") via `query_extractor`. Deterministic-first; a *minimal* single LLM extraction is allowed ONLY when the spec names no dataset explicitly.
3. For each intent, **query sources** in priority order (HF Hub → figshare/Zenodo/DataCite → Semantic Scholar/arXiv paper-data-links), gathering candidates.
4. For each candidate: **reachability** (verify.py) → if ok, **format-sniff** (sample-stream) → if it parses, mark **VERIFIED** with its detected format.
5. **Rank** verified candidates by (source authority, `query_relevance_score(intent, candidate_text)`); keep the **top-N** (default 3).
6. Emit the `ResolvedDatasets` manifest; `build_prompt` injects the top-N verified candidates per intent with: *"Cite ONLY these verified dataset URLs (prefer the first; you may cite more than one). Do NOT invent any dataset URL."*

## Manifest contract

Written to `projects/<id>/.specify/memory/resolved_datasets.yaml` (inspectable + cache-backed):

```yaml
resolved_at: <ISO-8601>
budget_s: 300
datasets:
  - intent: "QM9"
    status: verified            # verified | unresolved
    candidates:                 # top-N verified, best first (N default 3)
      - url: https://...
        source: huggingface|figshare|zenodo|datacite|semantic_scholar
        format: csv|parquet|hdf5|zip|xyz|...
        relevance: 0.0-1.0
        sample_check: {downloaded_bytes: N, parsed: true}
    candidates_tried:           # everything probed, incl. rejects (audit)
      - {url: ..., source: ..., status: reachable|unreachable|wrong_format, reason: ...}
```

An intent with zero verified candidates has `status: unresolved` and an empty `candidates` list
(but a populated `candidates_tried`).

## Error handling (Principle V — fail loud, never hallucinate)

- **No verified candidate for a required intent** → `status: unresolved`. The resolver does NOT
  fabricate a URL. The Planner is told the intent is unresolved and the project escalates to
  `human_input_needed` (writes `human_input_needed.yaml` listing unresolved intents + the
  `candidates_tried` evidence). This replaces the "planner invents URL → FR-006 rejects → retry"
  loop with "resolver searched real sources, found nothing reachable → human, with evidence."
- **Per-source API failure** → skip to the next source (reuse `search.py` exponential backoff);
  escalate only if ALL sources fail for an intent.
- **Budget**: resolver sub-budget (default 300s, separate from the planner's 900s); sample
  downloads capped at N MB with per-request timeouts.
- **Determinism on transient errors**: a transient network error on one candidate marks it
  `unreachable` (consistent with FR-006's no-retry stance) and moves on; it does not crash the run.

## Determinism boundary

- **Deterministic**: source search, reachability, format-sniff, ranking, top-N selection, manifest.
- **LLM**: only (a) optional dataset-intent extraction *when the spec names no dataset* (deterministic
  regex/keyword first), and (b) the Planner writing plan prose that *cites the provided* URLs. The
  "find a correct URL" task is fully removed from the LLM.

## Reuse (Principle I — single source of truth)

- Reachability: `librarian/verify.py._head_with_get_fallback` (do NOT reimplement).
- Relevance scoring: `verify.query_relevance_score` / `jaccard_tokens`.
- Paper search + rate-limit/backoff: `librarian/search.py` (`SemanticScholarClient`, arXiv, `_TokenBucket`, `_retry_request`).
- Caching: `librarian/cache.py`.
- Intent extraction: `librarian/query_extractor.py`.

## Testing (Principle III — real calls)

- **Real-call**: resolve "QM9" against HF Hub / figshare / Zenodo / DataCite / Semantic Scholar →
  assert ≥1 reachable, format-checked candidate is returned; assert top-N ordering is stable.
- **Local `http.server`**: serve a sample CSV / parquet / zip + a 404 + a wrong-format file →
  assert verified vs `unresolved` and correct format detection; reachability + sniff exercised for real (no mocks of the network path).
- **No-match escalation**: an intent whose every candidate is unreachable/wrong-format → `unresolved`
  + `human_input_needed.yaml` written.
- **Determinism**: identical inputs → identical selection (modulo live network).
- **Planner integration**: with a stubbed resolver returning a known verified URL, the Planner's
  `research.md` cites it and passes FR-006 end-to-end.

## Scope, files, dependencies

- New: `src/llmxive/librarian/dataset_resolver.py`, `src/llmxive/librarian/dataset_sources.py`.
- Edit: `src/llmxive/speckit/plan_cmd.py` (call resolver in `mechanical_step`; inject block in `build_prompt`).
- Edit: `agents/prompts/planner.md` (cite ONLY the provided verified dataset URLs; never invent).
- Tests: `tests/` unit + integration (real-call), following librarian test patterns.
- Dependency: `huggingface_hub` (verify it is already a project dependency; `hf` CLI is present) and `requests` (already present). Update `requirements`/`pyproject` only if `huggingface_hub` must be added.

## Relationship to spec-014 / FR-006

FR-006 (strict reachability) is unchanged and remains the safety net. With verified URLs injected,
the Planner's `research.md` cites only reachable, format-checked URLs, so FR-006 passes by
construction. This unblocks PROJ-262 and lets the spec-014 Phase-4 validation finish (PROJ-262 →
`analyzed`, carry-forward manifest, phase report).

## Out of scope / future

- Implementer-side reuse of the resolver for the actual bulk download (Approach C from brainstorming)
  — a natural follow-up, not part of this spec.
- General web-search backend for datasets absent from these registries.
