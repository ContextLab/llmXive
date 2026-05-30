# Tasks: Per-Claim Verification Modes (Approximate-Numeric, Computational, Magnitude/Relational)

**Input**: Design documents from `specs/018-approximate-numeric-verification/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/verification-modes.md, quickstart.md

**Tests**: REQUIRED — FR-013 mandates real-call verification; constitution III prohibits mock-only paths. The new modes (constants/compute/approximate/selector) are **deterministic**, so most of their tests are offline (real `sympy`/`scipy`/`math`, no mocks); LLM-classifier/locator + superlative/relational search are real-call gated.

**Organization**: grouped by user story. New code under `src/llmxive/verify/` + `fill/channels/constants.py`; modifications at the spec-016/017 wire-in points (contracts/research D6).

## Path Conventions

Single project. `src/llmxive/verify/{mode,approximate,compute,constants}.py`, `fill/channels/constants.py`; tests under `tests/{unit,integration,real_call}/`. The exact-count gate (`grounding.number_substantiated`/`number_appears_in`) is NOT modified (FR-003).

---

## Phase 1: Setup

- [X] T001 Create the verify package skeleton: `src/llmxive/verify/__init__.py` (re-exports `mode.select_mode`, `compute.verify_computational`, `constants.true_value`, `approximate.is_valid_rounding`).
- [ ] T002 Capture the baseline offline gate: `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs` and record the pass count (regression baseline; ~1680).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the mode selector + the constants/approximate primitives that the per-claim routing depends on.

- [X] T003 [P] Write failing unit test `tests/unit/test_verify_mode.py` for `verify/mode.py`: `looks_self_contained("1 plus 2 is 1")`/`("1 is larger than 2")` → True; `looks_self_contained("9,988 prime knots at 13 crossings")` → False; `looks_approximate("pi is about 3")`/`("the value is 3.14")` → True; `select_mode` (heuristic path, backend=None) returns "computational"/"approximate"/"exact"/"source" for representative claims; an integer discrete-count claim NEVER returns "approximate" (default-safe).
- [X] T004 Implement `src/llmxive/verify/mode.py`: pure `looks_self_contained`, `looks_approximate`, and `select_mode(claim, *, backend=None, model=None, repo_root=None) -> str` (hybrid: heuristics first; LLM tie-break ONLY when ambiguous AND a backend is present). `looks_self_contained` MUST return False when the claim references an external entity/subject (a *mixed* arithmetic+fact claim routes to `source`, never `computational` — FR-017: never verified by computation alone). Make T003 pass.
- [X] T005 [P] Write failing unit test `tests/unit/test_verify_constants.py` for `verify/constants.py`: `lookup("pi")`/`("π")`/`("speed of light")`/`("c")` resolve; `true_value("pi") == math.pi`, `true_value("e") == math.e`, `true_value("speed of light") == scipy.constants.c`; unknown subject → None; provenance names the authority + a url. (Deterministic, zero-network.)
- [X] T006 Implement `src/llmxive/verify/constants.py`: `CONSTANTS` table built from `math` (pi, e, tau, golden ratio) + `scipy.constants` (c, h, G, k, N_A, …) with aliases + citable authority/url; `lookup(subject)`, `true_value(subject)`. A self-test asserts values equal the library values (never hardcoded divergently). Make T005 pass.
- [X] T007 [P] Write failing unit test `tests/unit/test_verify_approximate.py` for `verify/approximate.py`: `parse_precision("3.14")` → decimals 2; `parse_precision("3")` → decimals 0; `has_hedge("pi is about 3")` → True; `is_valid_rounding(3.14, math.pi, decimals=2, hedge=False)` True; `is_valid_rounding(3, math.pi, decimals=0, hedge=True)` True; `is_valid_rounding(3.15, math.pi, decimals=2, hedge=False)` False; `is_valid_rounding(2.5, math.e, decimals=1, hedge=False)` False; `correction(math.e, decimals=1)` == "2.7". (Pure, numeric compare — never substring.)
- [X] T008 Implement `src/llmxive/verify/approximate.py`: `parse_precision`, `has_hedge`, `is_valid_rounding` (numeric round-to-stated-precision, ε-tolerant; hedge widens ±1 place), `correction` (round + format, no trailing "3.0"). Make T007 pass.

**Checkpoint**: mode selector + constants table + approximate comparator all green offline.

---

## Phase 3: User Story 1 — Approximate values verified by precision (Priority: P1) 🎯 MVP

**Goal**: an approximate/real-valued claim is judged by precision-aware rounding against a true value, not literal substring; the exact-count path is untouched.

**Independent Test**: "π is 3.14"/"about 3"/"3.14159" VERIFIED; "π is 3.15"/"e is 2.5" REFUTED+corrected; "9,988 prime knots" still exact-VERIFIED.

- [ ] T009 [US1] Make `src/llmxive/fill/extract.py::present_in_source` mode-aware: when the claim is approximate (per `verify.mode`/an approximate flag in evidence), compare the value via `verify.approximate.is_valid_rounding` against the number in `source.text`; otherwise keep the exact `number_substantiated` path UNCHANGED (FR-003).
- [ ] T010 [US1] Route approximate numeric claims in `src/llmxive/claims/resolve.py`: `resolve_numeric_or_citation` consults `verify.mode.select_mode`; an `approximate` claim gets its true value from `verify.constants.true_value` (Foundational T006) when the subject is a recognized constant, else from a fetched source; compares via the mode-aware gate; on a valid rounding → VERIFIED (value left as written, FR-007); on an invalid one → REFUTED then fill corrects to `approximate.correction(...)`. (Does NOT depend on the US2 channel wrapper — that is the fill-path integration in US2.)
- [ ] T011 [P] [US1] Write failing integration test `tests/integration/test_verify_approximate_wireup.py`: drive the resolve path (with a pre-built constants source / a real `verify.constants` value, no network) for "π is 3.14" → VERIFIED; "π is 3.15" → corrected to a sourced 3.14; and confirm "9,988 prime knots" still routes to the exact gate (no regression).
- [ ] T012 [P] [US1] Write failing real-call test `tests/real_call/test_verify_pi_e_real.py` (gated `LLMXIVE_REAL_TESTS`, but the constants path uses `verify.constants` — Foundational, zero-network — so most asserts run offline without the US2 channel): "π is 3.14"/"about 3"/"3.14159" VERIFIED; "π is 3.15"/"e is 2.5" REFUTED+corrected — all sourced from the library constants table with provenance; assert ZERO network calls for the constants path (SC-003).

**Checkpoint**: US1 independently testable — approximate verification works; exact counts unaffected.

---

## Phase 4: User Story 2 — Library-backed constants source (Priority: P1)

**Goal**: recognized constants resolve from the pre-seeded library table (zero network), as a high-authority fill channel.

**Independent Test**: π/e resolve from the table with no network; provenance names the authority.

- [ ] T013 [P] [US2] Write failing unit test `tests/unit/test_fill_constants_channel.py` for `fill/channels/constants.py`: `search_and_fetch("pi", claim)` returns one `FetchedSource(channel="constants", …, text contains the value + authority)`; an unknown subject → `[]`; no network.
- [ ] T014 [US2] Implement `src/llmxive/fill/channels/constants.py::search_and_fetch` wrapping `verify.constants` → `FetchedSource`; register it in `fill/service.py::_get_channel("constants")` and add `AUTHORITY["constants"]` as the **top authority rank** (≤ `oeis`=0, e.g. 0 or -1) so a recognized constant's library value wins any conflict (FR-005: highest-authority source) + route it into NUMERIC/approximate `channels_for` in `fill/channels/__init__.py`. Make T013 pass.
- [ ] T015 [P] [US2] Write failing integration test `tests/integration/test_constants_zero_network.py`: a fill for an approximate constant claim uses the constants channel and performs no HTTP (assert via a counter wrapping the real `_retry_request`/channel HTTP staying flat), with provenance naming the authority.

**Checkpoint**: US2 independently testable — constants resolve deterministically, zero network.

---

## Phase 5: User Story 5 — Computational verification by evaluation (Priority: P1)

**Goal**: self-contained claims are evaluated with safe `sympy` and verified/corrected by computation — catching "1 plus 2 is 1" and "1 is larger than 2" as WRONG.

**Independent Test**: "1 plus 1 is 2" VERIFIED; "1 plus 2 is 1" REFUTED→3; "1 is larger than 2" REFUTED; "30% of 200 is 60" VERIFIED; "5 km is 5,200 m" REFUTED→5,000 m — all by computation, no source/LLM-asserted result.

- [ ] T016 [P] [US5] Write failing unit test `tests/unit/test_verify_compute.py` for `verify/compute.py::evaluate`: `evaluate("1+2")=="3"`, `evaluate("1>2")` falsy, `evaluate("(x+1)**2 - (x**2+2*x+1)")=="0"` (identity), unit conversion "5 km → m" == "5000"; an unparseable/unsafe input → None (never raises, never `eval`). PURE/deterministic, real sympy, NO mocks.
- [ ] T017 [US5] Implement `src/llmxive/verify/compute.py`: `evaluate(expression) -> str | None` (restricted `sympy` parsing — NO `eval`/`exec`; arithmetic, comparisons, percentages, `sympy.physics.units` conversions, `simplify` identities, `sympy.logic`/`sympy.sets`); `extract_expression(claim, *, backend, model, repo_root) -> (expr, asserted) | None` (LLM locator only — it NEVER computes); `verify_computational(claim, ...) -> ComputeVerdict` (verified iff asserted==computed, reusing approximate tolerance when real-valued; not_evaluable → caller falls back). Make T016 pass.
- [ ] T018 [US5] Route computational claims in `src/llmxive/claims/resolve.py`: when `select_mode` returns "computational", call `verify.compute.verify_computational`; VERIFIED (evidence: expression+computed, resolver="compute") on match; REFUTED → fill substitutes the computed value (render + citation-repair the computation as provenance); `not_evaluable` → fall through to the source path. RESULT-kind claims are never routed to compute.
- [ ] T019 [P] [US5] Write failing real-call test `tests/real_call/test_compute_real.py` (gated; the evaluation is deterministic, only the expression-locator needs the backend): "1 plus 1 is 2" VERIFIED; "1 plus 2 is 1" REFUTED and corrected to 3; "1 is larger than 2" REFUTED; "30% of 200 is 60" VERIFIED; "5 km is 5,200 m" REFUTED+corrected to 5,000 m; provenance is the evaluated expression; assert the computed value came from sympy, not the model (SC-010).

**Checkpoint**: US5 independently testable — the computational hole is closed.

---

## Phase 6: User Story 3 — Magnitude/superlative fills (Priority: P2)

**Goal**: enable MAGNITUDE fills — correct a wrong superlative from a retrieved candidate set, or block.

**Independent Test**: "the largest planet is Saturn" → Jupiter; no candidate set → blocked.

- [ ] T020 [US3] Enable MAGNITUDE fill: `fill/service.py::_FILLABLE_KINDS += {MAGNITUDE}`; `fill/channels/__init__.py::channels_for(MAGNITUDE)` → `[wikidata, wikipedia, paper]`; wire `_maybe_fill` into `claims/resolve.py` at `resolve_magnitude`'s NEI/REFUTED return sites (reuse the existing helper).
- [ ] T021 [P] [US3] Write failing integration test `tests/integration/test_fill_magnitude_wireup.py`: with the flag on and a real `FillResult.filled` injected at the seam (real object, not a mock backend), a MAGNITUDE claim that would be NEI returns VERIFIED with the corrected extremum + evidence.filled; flag off → unchanged.
- [ ] T022 [P] [US3] Write failing real-call test `tests/real_call/test_fill_superlative_real.py` (gated): "the largest planet is Saturn" → corrected to "Jupiter" from a fetched candidate set with provenance; a superlative with no retrievable set → blocked.

**Checkpoint**: US3 independently testable — superlatives corrected or blocked.

---

## Phase 7: User Story 4 — Set/relational fills (Priority: P2)

**Goal**: enable RELATIONAL fills — correct a wrong relation's object from a structured source, or block; a multi-valued relation is not over-corrected.

**Independent Test**: "the capital of Australia is Sydney" → Canberra; multi-valued relation with a valid claimed object → VERIFIED; unsourceable → blocked.

- [ ] T023 [US4] Enable RELATIONAL fill: `_FILLABLE_KINDS += {RELATIONAL}`; `channels_for(RELATIONAL)` → `[wikidata, wikipedia, paper]`; wire `_maybe_fill` into `claims/resolve.py` at `resolve_relational`'s NEI/REFUTED sites; ensure a claimed object that is one of several sourced-valid objects is VERIFIED (not over-corrected) — FR-009.
- [ ] T024 [P] [US4] Write failing integration test `tests/integration/test_fill_relational_wireup.py`: a RELATIONAL claim filled (real FillResult at the seam) → VERIFIED with corrected object; the multi-valued-relation case (claimed object ∈ sourced set) → VERIFIED, not corrected.
- [ ] T025 [P] [US4] Write failing real-call test `tests/real_call/test_fill_relational_real.py` (gated): "the capital of Australia is Sydney" → corrected to "Canberra" (triple form) with Wikidata/Wikipedia provenance; an unsourceable relation → blocked.

**Checkpoint**: US4 independently testable — relations corrected/verified/blocked correctly.

---

## Phase 8: Polish & Cross-Cutting

- [ ] T026 Enable the spec-018 modes on real runs: `src/llmxive/cli.py::run` adds the needed `os.environ.setdefault(...)` (mirroring the spec-016/017 flags) so mode selection + compute + constants are active in production; confirm offline tests stay network-free.
- [ ] T027 [P] Write failing integration test `tests/integration/test_exact_count_no_regress.py`: "9,988 prime knots at 13 crossings" is mode-selected EXACT and verified by the unchanged `number_substantiated` gate (SC-002) — guards against an approximate/computational misroute loosening a count.
- [ ] T028 Run the FULL offline gate (`pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`) and the gated real-call suite (`LLMXIVE_REAL_TESTS=1 pytest tests/real_call/test_verify_*_real.py tests/real_call/test_compute_real.py tests/real_call/test_fill_superlative_real.py tests/real_call/test_fill_relational_real.py -q`); also re-run the spec-017 fill e2e to confirm no regression. Fix CODE (never tests) until green vs the T002 baseline.
- [ ] T029 Update `quickstart.md` only if a public signature drifted; confirm SC-001…SC-010 each map to a passing test.

---

## Dependencies & Execution Order

- **Setup → Foundational** block everything (mode selector + constants + approximate primitives).
- **US1 (approximate)** depends on Foundational; uses US2's constants channel for the true value (so US2 lands with/before US1's real-call).
- **US2 (constants)** depends on Foundational (`verify/constants`).
- **US5 (computational)** depends on Foundational (`verify/compute` + mode selector); independent of US1/US2.
- **US3/US4 (magnitude/relational)** depend only on the spec-017 fill + spec-016 triple (already built); independent of the numeric modes.
- **Polish** depends on all stories.

## Parallel Opportunities

- Phase 2: T003/T005/T007 test files parallel; impls follow.
- US2's constants channel + US5's compute evaluator + US3/US4's fill enablement touch different files → parallel after Foundational.
- Real-call tests across stories are independent.

## Implementation Strategy

**MVP = Setup + Foundational + US1 + US2 + US5** (the three P1 verification modes — approximate, constants, computational — which close the maintainer-flagged gaps incl. "1 plus 2 is 1"). Then US3/US4 (the 017 magnitude/relational fast-follow), then Polish (cli flag, no-regress guard, full gates). Deterministic modes are tested offline with real libraries; LLM-classifier/locator + superlative/relational search are real-call gated. The exact gate is never modified (FR-003).
