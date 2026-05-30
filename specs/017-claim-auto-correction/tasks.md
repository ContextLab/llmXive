# Tasks: Authoritative-Fill / Claim Auto-Correction

**Input**: Design documents from `specs/017-claim-auto-correction/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/fill-layer.md, quickstart.md

**Tests**: REQUIRED — the spec mandates real-call verification (FR-013) and the constitution (III) prohibits mock-only paths. Each story gets real-call + offline pure-logic tests.

**Organization**: grouped by user story (US1–US4). New code under `src/llmxive/fill/`; existing modules modified at the wire-in points in `contracts/fill-layer.md`.

## Path Conventions

Single project. New package `src/llmxive/fill/` (+ `channels/`); tests under `tests/{unit,contract,integration,real_call}/`. All search/fetch/presence-gate/cache/citation machinery is reused from `librarian/`, `grounding/`, `agents/citation_guard.py` per the reuse map (research D9).

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create the fill package skeleton: `src/llmxive/fill/__init__.py` (re-exports `service.fill_claim`) and `src/llmxive/fill/channels/__init__.py`.
- [ ] T002 Capture the baseline offline gate: run `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs` and record the pass count (regression baseline; currently ~1511).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: entities + pure logic every story depends on. No story proceeds until these are green.

- [X] T003 [P] Write failing unit test `tests/unit/test_fill_models.py` for `fill/models.py`: `FetchedSource`, `FillProvenance`, `FillResult` construct/validate; `FillResult.status in {"filled","blocked"}`; a `filled` result requires non-null value+provenance.
- [X] T004 Implement `src/llmxive/fill/models.py` (frozen dataclasses per data-model.md). Make T003 pass.
- [X] T005 [P] Write failing unit test `tests/unit/test_fill_subject_query.py` for `fill/subject_query.py::strip_asserted_value`: "27,635 prime knots at 13 crossings" with value "27635"/"27,635" → query keeps "prime knots"/"13 crossings", drops the number (pure, deterministic, no backend).
- [X] T006 Implement `src/llmxive/fill/subject_query.py`: pure `strip_asserted_value(raw_text, value)` + `subject_query(claim, *, backend=None, model=None, repo_root=None)` (falls back to the pure strip when no backend). Make T005 pass.
- [X] T007 [P] Write failing unit test `tests/unit/test_fill_extract_gate.py` for `fill/extract.py::present_in_source`: numeric delegates to `grounding.service.number_substantiated` (True when the value is in `source.text`, False when absent); entity uses a normalized located-in-text check (real strings, NO mock backend — this is the safety gate).
- [X] T008 Implement `src/llmxive/fill/extract.py`: `present_in_source(value, source, kind)` (deterministic, reuses `number_substantiated`) and `extract_value(source, claim, *, backend, model, repo_root)` (LLM locator that returns a candidate ONLY if `present_in_source` passes — returns None otherwise). Make T007 pass; the LLM path is exercised real in US1/US2.
- [X] T009 [P] Write failing unit test `tests/unit/test_fill_conflict.py` for `fill/conflict.py::choose`: given (source, value) pairs from channels of differing `authority`, returns the highest-authority value + the `conflicts` list of lower-authority disagreements; never drops a conflict (pure).
- [X] T010 Implement `src/llmxive/fill/conflict.py` + the `AUTHORITY` map and `channels_for(kind, *, math)` routing in `src/llmxive/fill/channels/__init__.py` (oeis<wikidata<wikipedia<theorem<paper; v1 routes numeric→[oeis,wikipedia,paper(,theorem if math)], entity→[wikidata,wikipedia,paper], others→[]). Make T009 pass.
- [X] T011 [P] Write failing unit test `tests/unit/test_fill_citation_repair.py` for `fill/citation_repair.py::repair_citation`: given doc text with a claim value + a stale/free-text citation and a `FillProvenance`, the citation adjacent to the value is rewritten/annotated to the authoritative source (e.g. `(OEIS A002863, oeis.org/A002863)`); idempotent; unrelated prose untouched (pure; reuse `agents/citation_guard` occurrence regexes).
- [X] T012 Implement `src/llmxive/fill/citation_repair.py`. Make T011 pass.

**Checkpoint**: models, pure subject-query, the present-in-source gate, conflict ordering, channel routing, and citation repair all green offline.

---

## Phase 3: User Story 1 — A fabricated value is auto-corrected from a real source (Priority: P1) 🎯 MVP

**Goal**: numeric claims that can't be verified are corrected from a real source (OEIS via b-file, surfaced by Wikipedia) and substituted, with provenance. The headline 27,635→9,988 path.

**Independent Test**: run the fill on the "27,635 prime knots at 13 crossings" claim; the rendered output shows 9,988 from a resolvable source with provenance, never 27,635, no human input.

- [X] T013 [P] [US1] Write failing unit test `tests/unit/test_fill_oeis_parse.py` for `fill/channels/oeis.py`: `a_numbers_in("… OEIS A002863 …")` → `["A002863"]` (pure); and a b-file-text parser turns `"13 9988\n14 46972"` lines into `{13:9988, 14:46972}` (pure parse, no network).
- [X] T014 [US1] Implement `src/llmxive/fill/channels/oeis.py`: pure `a_numbers_in(text)` + b-file parser; `fetch_bfile(a_number, *, timeout=20.0)` (REAL http to `https://oeis.org/<A>/b<num>.txt` via the librarian `_retry_request`/UA pattern — the search API is Cloudflare-blocked, research D1); `search_and_fetch(query, claim)` → `FetchedSource`s (resolve A-numbers found in the claim/query text, fetch their b-files; returns `[]` on HTTP failure). Make T013 pass.
- [X] T015 [P] [US1] Write failing unit test `tests/unit/test_fill_wikipedia_parse.py` for `fill/channels/wikipedia.py`: the search-result and extract JSON parsers turn captured-fixture API responses into article titles / plain-text extracts (pure parse, no network).
- [X] T016 [US1] Implement `src/llmxive/fill/channels/wikipedia.py`: `search_and_fetch(query, claim)` — real Wikipedia `action=query&list=search` then `prop=extracts&explaintext=1` (via `_retry_request` + UA), returning `FetchedSource`s with the article extract text + URL; `[]` on failure. Make T015 pass.
- [X] T017 [US1] Implement `src/llmxive/fill/channels/papers.py` + `theorem.py`: adapt librarian `SemanticScholarClient.search_papers`/`ArxivClient.search` (papers) and `TheoremSearchClient.search` (math claims, via `math_classifier.classify`) candidates to `FetchedSource` by fetching text with `grounding.full_text.retrieve`; `[]` on failure.
- [X] T018 [US1] Implement `src/llmxive/fill/service.py::fill_claim(claim, *, backend, model, repo_root) -> FillResult`: subject_query → `channels_for(kind)` search_and_fetch → **cross-channel OEIS enrichment** (run `oeis.a_numbers_in()` over the discovery channels' fetched text — e.g. Wikipedia surfaces A002863 for the knot count, research D1/D2 — and `oeis.fetch_bfile()` to add the higher-authority OEIS `FetchedSource` before conflict resolution) → `extract_value` (present-in-source gate) per source → `conflict.choose` (OEIS outranks Wikipedia) → FillResult(filled, value, provenance) | FillResult(blocked, reason). The bounded channel list IS the per-attempt budget (FR-011): each channel is tried at most once, then the claim is blocked (no unbounded retry; cross-round retry is governed by the spec-016 kickback budget). Cache by (canonical, channel) via `grounding/cache`. v1: numeric + entity only; others → blocked. Update `fill/__init__.py` re-export.
- [X] T019 [US1] Wire fill into `src/llmxive/claims/resolve.py::resolve_numeric_or_citation`: when `LLMXIVE_CLAIM_FILL=1` and the resolver would return NOT_ENOUGH_INFO/REFUTED, call `fill.service.fill_claim`; on `filled` return `Verdict(VERIFIED, value=<corrected>, evidence={"filled":True,"fill":{…}}, resolver="fill:<channel>")`; on blocked return the original Verdict. Never fill a RESULT claim.
- [X] T020 [P] [US1] Write failing integration test `tests/integration/test_fill_resolve_wireup.py`: with `LLMXIVE_CLAIM_FILL=1` and a fill service that returns a known `filled` result for a fixed claim (drive the REAL resolve.py branch; inject the fill at the seam via a real `FillResult`, not a mock backend), `resolve()` returns VERIFIED with the corrected value + `evidence.filled`; with the flag off, behavior is unchanged (still NEI).
- [X] T021 [P] [US1] Write failing real-call test `tests/real_call/test_fill_oeis_real.py` (gated `LLMXIVE_REAL_TESTS`): `oeis.fetch_bfile("A002863")[13] == 9988` (real OEIS b-file); and `fill_claim` on a claim mentioning A002863 at 13 crossings → filled value "9988" with OEIS provenance.
- [X] T022 [P] [US1] Write failing real-call test `tests/real_call/test_fill_wikipedia_real.py` (gated): Wikipedia `search_and_fetch("number of prime knots by crossing number")` returns a fetched article whose text contains "9988" AND surfaces an OEIS A-number (A002863); `fill_claim` corrects the knot-count claim to 9988 with provenance — OEIS via the cross-channel bridge when the A-number is surfaced (highest authority), else Wikipedia as the resolvable source (FR-014/SC-001 accept either resolvable source).
- [X] T023 [US1] Write failing real-call e2e `tests/real_call/test_fill_e2e_real.py` (gated): drive the real chokepoint (`speckit.slash_command._validate_artifact_citations`) with `LLMXIVE_CLAIM_FILL=1` on an artifact carrying "27,635 prime knots at 13 crossings"; assert the rendered artifact shows 9,988 (from a resolvable source), never 27,635, and no human-input request. WebFetch/verify any asserted source URL first.

**Checkpoint**: US1 independently testable — the headline fabrication is auto-corrected from a real source.

---

## Phase 4: User Story 2 — Filled value always traceable to a fetched source, never model memory (Priority: P1)

**Goal**: the present-in-source gate is the hard boundary; a value not in any fetched source is rejected and the claim stays blocked, with provenance on every successful fill.

**Independent Test**: force a source whose text lacks the candidate value → no fill, stays blocked; inspect a successful fill → provenance present + value located in source.

- [ ] T024 [P] [US2] Write failing unit test `tests/unit/test_fill_rejects_absent_value.py`: `extract_value` returns None when the LLM-proposed value is NOT in `source.text` (construct a real `FetchedSource` whose text lacks the value; assert the gate rejects it) — the safety property, offline + deterministic.
- [ ] T025 [US2] Harden `fill/service.fill_claim` so a candidate that fails `present_in_source` for ALL fetched sources yields `FillResult(blocked, reason="value not present in any fetched source")` and records `channels_tried`; ensure provenance is only ever built from a source whose text contains the value. Make T024 pass.
- [ ] T026 [P] [US2] Write failing real-call test `tests/real_call/test_fill_no_source_blocks_real.py` (gated): a claim with a genuinely-unsourceable value (e.g. a fabricated count for a nonexistent subject) → `fill_claim` returns blocked (no fabricated fill); the claim stays NEI.
- [ ] T027 [US2] Add a provenance-inspection assertion to `tests/real_call/test_fill_oeis_real.py` (or a sibling): every successful fill carries `provenance.url` (resolvable) + `provenance.quote` and the value is literally in the fetched source text (SC-002).

**Checkpoint**: US2 independently testable — zero fills from model memory; unsourceable values stay blocked.

---

## Phase 5: User Story 3 — Non-numeric (entity) claims are corrected too (Priority: P2)

**Goal**: entity/definitional claims are filled from Wikidata/Wikipedia (v1 scope: entity; relational/superlative deferred).

**Independent Test**: a wrong entity/definitional claim with a discoverable source is corrected with provenance; a deferred-type (relational/superlative) claim is confirmed to stay blocked (not falsely filled).

- [ ] T028 [P] [US3] Write failing unit test `tests/unit/test_fill_wikidata_parse.py` for `fill/channels/wikidata.py`: the `wbsearchentities` + entity-fetch JSON parsers turn captured fixtures into `FetchedSource`s (entity label/description/statement text) (pure parse, no network).
- [ ] T029 [US3] Implement `src/llmxive/fill/channels/wikidata.py`: `search_and_fetch(query, claim)` — real Wikidata `wbsearchentities` then entity fetch (via `_retry_request` + UA), returning `FetchedSource`s with entity statement/description text + URL; `[]` on failure. Make T028 pass.
- [ ] T030 [US3] Wire fill into `src/llmxive/claims/resolve.py::resolve_entity_fact` (same pattern as T019, at its NEI branches lines 287/321); confirm `channels_for` routes entity → [wikidata, wikipedia, paper] and that magnitude/relational kinds are NOT routed (return blocked, stay blocked).
- [ ] T031 [P] [US3] Write failing real-call test `tests/real_call/test_fill_wikidata_real.py` (gated): a wrong entity/definitional claim (e.g. a wrong capital-of-country or a wrong definitional value) is corrected to the sourced answer with Wikidata/Wikipedia provenance; and a relational/superlative claim is confirmed to stay blocked in v1 (no fill).

**Checkpoint**: US3 independently testable — entity claims corrected; deferred types remain blocked, never falsely filled.

---

## Phase 6: User Story 4 — Corrected values reused "for free" and never drift (Priority: P3)

**Goal**: a filled value is cached, reused across rounds/documents without re-searching, and invalidated when the source changes.

**Independent Test**: fill once; reference again → identical cached value, no new search; change the source → invalidated + re-derived.

- [ ] T032 [P] [US4] Write failing integration test `tests/integration/test_fill_reuse.py`: a claim filled once and persisted VERIFIED (with `source_hash` from the fill source) is reused on a second pass with NO new channel search (assert via the real grounding cache being hit / a counter wrapping the REAL `fill_claim` staying flat — not a mock); changing the recorded `source_hash` forces a re-fill.
- [ ] T033 [US4] Implement fill-result caching + source_hash in `fill/service.fill_claim` and ensure `claims/service.resolve_registered_claims` reuse/invalidation (spec-016) applies to filled claims (set `Claim.source_hash` from the fill source). Make T032 pass.

**Checkpoint**: US4 independently testable — filled values reused and invalidated correctly.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T034 [P] Write failing integration test `tests/integration/test_fill_render_repairs_citation.py`: after `claims/service.process_document` renders a filled claim, the rendered text cites the corrected value to its fill source (FR-007/SC-008) — drive with a pre-built registry containing a filled claim (offline; real `repair_citation`).
- [ ] T035 Wire citation repair into `src/llmxive/claims/service.py::process_document`: after `render`, for each claim with `evidence.filled` true, call `fill.citation_repair.repair_citation` on the rendered text. Make T034 pass.
- [ ] T036 Enable the fill on real runs: `src/llmxive/cli.py::run` adds `os.environ.setdefault("LLMXIVE_CLAIM_FILL", "1")` (mirrors LLMXIVE_CLAIM_LAYER); confirm offline reviser/cli tests stay network-free (the flag is unset for them).
- [ ] T037 [P] Write failing contract test `tests/contract/test_fill_channel_contract.py`: each channel's `search_and_fetch` returns `FetchedSource`s with non-empty `text` + resolvable `url` (run real-call gated for the network part; offline asserts the parse contract on fixtures).
- [ ] T038 Run the full offline gate (`pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`) and the gated real-call suite (`LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_fill_*_real.py -q`); fix code (never tests) until green vs the T002 baseline.
- [ ] T039 Update `quickstart.md` only if a public signature drifted during implementation; confirm SC-001…SC-008 each map to a passing test.

---

## Dependencies & Execution Order

- **Setup (P1)** → **Foundational (P2)** block everything.
- **US1 (P3)** is the MVP; depends only on Foundational. Deliverable on its own (numeric fill, headline scenario).
- **US2 (P4)** hardens US1's gate + adds safety tests; depends on US1's `service.fill_claim`.
- **US3 (P5)** adds the Wikidata channel + entity wire-in; depends on Foundational + `service.fill_claim`.
- **US4 (P6)** depends on US1 (a filled claim to reuse).
- **Polish (P7)** depends on US1–US4 surfaces; citation-repair wire-in (T034/T035) needs `claims/service`; cli flag (T036) independent.

## Parallel Opportunities

- Phase 2: T003/T005/T007/T009/T011 (distinct test files) in parallel; each impl follows its test.
- Within US1: channel impls `oeis.py`/`wikipedia.py`/`papers.py` touch different files → parallel; `service.py`/`resolve.py` wiring is sequential.
- Across stories: US3's Wikidata channel can proceed in parallel with US1 once Foundational is done (different files).

## Implementation Strategy

**MVP = Phase 1 + 2 + US1** — numeric auto-correction with the OEIS/Wikipedia path; the headline 27,635→9,988 e2e is the acceptance test. Then US2 (safety hardening + tests), US3 (entity/Wikidata), US4 (reuse), Polish (citation repair, cli flag, full gates). Tests precede implementation in each pair; real-call tests gated by `LLMXIVE_REAL_TESTS`; the present-in-source gate is the non-negotiable trust boundary throughout.
