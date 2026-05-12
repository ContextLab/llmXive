# Phase 1 Data Model — spec 006 (TheoremSearch backend + mathematics field)

This extends spec 005's data model (`specs/005-librarian-agent/data-model.md`). Only the *new* and *changed* entities are described here; all spec-005 entities are unchanged except `LibrarianResult` (gains one field) and the cross-domain test-row (may gain one optional field). Entity IDs are prefixed `E-TS#` to distinguish from spec-005's `E#`.

---

## E-TS1 — TheoremSearch theorem hit (transient; not persisted)

A single record in the `theorems` array of a `POST /search` response.

| Field | Type | Notes |
|-|-|-|
| `theorem_id` | int | Ignored by the librarian (Spec B territory). |
| `name`, `body`, `slogan`, `theorem_type`, `label`, `link` | str / null | Ignored by the librarian. |
| `paper` | object | **The only sub-object the librarian reads.** See below. |
| `similarity`, `score` | float | `score` used only for ordering (descending) before the per-hit `limit` cut. |
| `has_metadata` | bool | Informational; not relied upon. |

`paper` sub-object:

| Field | Type | Notes |
|-|-|-|
| `paper_id` | str | For `source == "arXiv"`: the versioned arXiv ID, e.g. `"1306.5434v2"`. For ProofWiki: `"proofwiki"` (not a real ID). |
| `source` | str | Enum seen: `"arXiv"`, `"ProofWiki"`, `"Stacks Project"`, … The librarian processes **only** `"arXiv"`; everything else is skipped. |
| `title` | str | Used as a sanity check only; the authoritative title comes from `ArxivClient.get_by_id`. |
| `authors` | list[str] | Empty for non-arXiv sources. Not used (the arXiv resolver provides authors). |
| `link` | str | For arXiv: `"http://arxiv.org/abs/<id>"`. For ProofWiki: the wiki URL. |
| `year`, `journal_ref`, `primary_category`, `categories`, `citations`, `journal_published` | various | Not used by the librarian (the arXiv resolver provides year etc.). |

**Lifecycle**: created when parsing a `/search` response; lives only for the duration of one `TheoremSearchClient.search()` call. Never written to disk (the *resolved* `Candidate` it produces flows into the librarian's normal pipeline; the cached `LibrarianResult` is what persists).

**Validation rules**: a hit is *usable* iff `paper.source == "arXiv"` AND `paper.paper_id` matches `^\d{4}\.\d{4,5}(v\d+)?$` (modern arXiv ID, optionally versioned) — older-style IDs (`hep-th/9901001`) are also accepted if `_arxiv_short_id` can normalize them. Hits that fail this are skipped (logged at debug).

---

## E-TS2 — TheoremSearch-sourced Candidate (the bridge to the existing pipeline)

A librarian `Candidate` (spec-005 E2 — `{backend, primary_pointer, claimed_title, claimed_authors, claimed_year, claimed_venue, claimed_abstract}`) produced from a usable E-TS1 hit by resolving its arXiv ID.

| Field | Value | Notes |
|-|-|-|
| `backend` | `"theoremsearch"` | **The one distinguishing field.** Set by re-tagging the `Candidate` that `ArxivClient.get_by_id` returns (which comes back tagged `"arxiv"`). |
| `primary_pointer` | the resolver-normalized arXiv short ID | Taken from the resolved `Candidate.primary_pointer`, NOT from the raw `paper.paper_id` — so it matches what an arXiv-search-sourced copy of the same paper would have, enabling dedup. |
| `claimed_title` | from `ArxivClient.get_by_id` | Authoritative arXiv title. |
| `claimed_authors` | from `ArxivClient.get_by_id` | |
| `claimed_year` | from `ArxivClient.get_by_id` | |
| `claimed_venue` | `"arXiv"` | (Same as an arXiv-sourced candidate.) |
| `claimed_abstract` | from `ArxivClient.get_by_id` | Authoritative arXiv abstract; needed by the verification chain's summary-grounding check. |

**Lifecycle**: created inside `TheoremSearchClient.search()` (one per usable hit, after `get_by_id` succeeds); appended to the librarian's `candidates` list (subject to dedup by `primary_pointer` against SS/arXiv candidates); flows through `_verify_each` → `_maybe_expand` → relevance judge → PDF sample exactly like any candidate; if it survives, it appears in `LibrarianResult.verified_citations` with its verification log recording `backend="theoremsearch"`.

**Validation / failure handling**: if `ArxivClient.get_by_id(stripped_id)` returns `None`, no `Candidate` is produced for that hit (logged warning) — same as any unresolvable arXiv candidate. If the whole `TheoremSearchClient.search()` raises `TransientBackendError`, the caller (`_theoremsearch_candidates` in `librarian.py`) returns `[]` — zero TheoremSearch contribution that run; the librarian completes on SS+arXiv.

**Relationship to spec-005 E2**: `Candidate` is *unchanged*. `backend` was always a free-text str; `"theoremsearch"` is just a new value. Downstream code that branches on `backend` (currently nothing does, except logging) sees it as a normal candidate.

---

## E-TS3 — MathClassifierResult (in-memory) / `math_classifier` audit object (serialized)

The outcome of the math-classifier decision for one librarian invocation.

In-memory record (returned by `math_classifier.classify(...)`):

| Field | Type | Notes |
|-|-|-|
| `invoked` | bool | `False` when the `field == "mathematics"` unconditional trigger fired (the classifier LLM was *not* called). `True` when a non-math field caused the classifier to be consulted (whether the call succeeded or failed). |
| `verdict` | bool \| None | The boolean ("is this a pure-math theorem/proof/formal-structure question?") when the classifier ran successfully. `None` when `invoked == False` (skipped) OR when the classifier call failed. |
| `error` | str \| None | The failure message string when the classifier call errored; `None` otherwise. |
| `cached` | bool | `True` if `verdict` came from the per-project cache (no LLM call this run); `False` if freshly computed (or if `invoked == False`). **In-memory only — dropped from the serialized form.** |

Serialized form — the `math_classifier` field in `LibrarianResult.to_dict()` output JSON: `{"invoked": bool, "verdict": bool | null, "error": str | null}`. (Drops `cached`.) Parallel to the existing `relevance_judge` and `pdf_sample` audit objects in that same JSON.

**Lifecycle**: computed once per `LibrarianAgent.invoke()` call; embedded in the returned `LibrarianResult`; serialized into the cached `LibrarianResult` JSON; on a cache-hit re-run the cached value is replayed (no re-classification — but note: a cache hit on the *result* cache means the *whole* `LibrarianResult` including its `math_classifier` field is replayed; the *classifier-verdict* cache (E-TS4) is a separate, finer-grained cache that matters when the result cache misses but the project's classifier verdict is still valid).

**Truth table**:

| Trigger | `invoked` | `verdict` | `error` | `cached` (in-mem) |
|-|-|-|-|-|
| `field == "mathematics"` | `false` | `null` | `null` | `false` |
| non-math field, classifier hit cache | `true` | `true`/`false` (cached) | `null` | `true` |
| non-math field, classifier ran, success | `true` | `true`/`false` | `null` | `false` |
| non-math field, classifier ran, failed | `true` | `null` | `"<msg>"` | `false` |

---

## E-TS4 — Math-classifier verdict cache entry (persisted)

One entry in `state/librarian-cache/math-classifier-verdicts.json` (a flat dict).

| Key | Value |
|-|-|
| `f"{project_id}::{librarian_prompt_version}"` | `{"verdict": bool, "classified_at": "<ISO-8601 UTC>"}` |

**Lifecycle**: written when a non-math-field librarian invocation with a `project_id` runs the classifier successfully (and the key wasn't already present); read at the start of the math-classifier step on subsequent invocations of the librarian on the same project under the same `librarian_prompt_version`. A `prompt_version` bump changes the key suffix → old entries become unreachable (effectively invalidated; a re-run re-classifies). When `project_id` is `None` (standalone smoke test), nothing is written or read.

**Validation**: the file is a JSON object (created empty `{}` if absent); a malformed file is treated as empty (logged, then overwritten on the next write) — failing soft, consistent with the librarian's cache philosophy.

**Why a separate cache from the result cache (E5 in spec 005)**: the result cache is keyed by `sha256(normalized_term)` and stores whole `LibrarianResult`s; it captures everything. The verdict cache is keyed by `(project_id, prompt_version)` and stores just a boolean; it's the thing that lets a *second* librarian call on the same project — even with a slightly reworded question that misses the result cache — skip the classifier LLM call. Per Clarifications 2026-05-12.

---

## E-TS5 — Seed math project

A brainstormed project with `field: mathematics` — 5 of them, created via the existing brainstorm agent after `mathematics` is added to the field lists. **No special structure**: identical shape to any other brainstormed project (`projects/PROJ-###-<slug>/idea/<slug>.md`, `state/projects/PROJ-###-<slug>.yaml` with `field: mathematics`, etc.).

**Lifecycle**: created during this amendment's implementation (after FR-A09's field-list change); thereafter indistinguishable from any project. The cross-domain coverage test's `mathematics` parametrization picks the most-recently-brainstormed `mathematics` project (the existing per-field selection logic) and invokes the librarian on it.

**Validation**: each must have `field: mathematics` in its `state/projects/PROJ-###-*.yaml`; ≥5 must exist (SC-A06).

---

## Changed spec-005 entities (summary)

- **`LibrarianResult` (spec-005 E5)**: gains exactly one new field — `math_classifier` (the E-TS3 serialized form). Everything else (`schema_version`, `librarian_prompt_version`, `term_input`, `context`, `outcome`, `verified_citations`, `verification_failures`, `expansion`, `pdf_sample`, `relevance_judge`, `extracted_queries`, `per_query_hit_count`, `started_at`, `ended_at`, `duration_seconds`, `cache_status`) unchanged. The `verified_citations` entries are unchanged in shape; a TheoremSearch-sourced one is identifiable by its `verification_log` recording `backend="theoremsearch"` (the verification log already records the candidate's backend).
- **Cross-domain test-row (spec-005's `CrossDomainTestRow`)**: MAY gain an optional `theoremsearch_hit_count: int` field (how many candidates the TheoremSearch backend contributed) for the diagnostic — but this is a test artifact, not part of the librarian's contract. Decided at /speckit-tasks whether to add it.
- **`Candidate` (spec-005 E2)**: unchanged. `backend` gains a new possible value (`"theoremsearch"`).
- **Everything else in spec-005's data model**: unchanged.
