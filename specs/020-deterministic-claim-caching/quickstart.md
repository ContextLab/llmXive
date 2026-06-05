# Quickstart: Verifying spec 020 (Deterministic Claim Caching + Planning Reference-Only)

This is the verification matrix the implementation must satisfy. Offline tests pin the deterministic
logic; real-call tests exercise the externally-dependent paths with **free** Dartmouth models only
(per Principle IV + the free-only guard).

## Prerequisites

```bash
cd /Users/jmanning/llmXive
# Offline gate (no network/model needed):
python -m pytest tests/unit tests/integration tests/contract -q -p no:cacheprovider \
  --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs

# Real-call tests (free models only; key auto-resolved via llmxive.credentials.load_dartmouth_key):
export LLMXIVE_REAL_TESTS=1
```

## A. Offline determinism (fast feedback — must pass in CI without network)

| # | What it proves | Command |
|-|-|-|
| A1 | `is_planning_stage` truth table (FR-001) | `pytest tests/unit/test_stage_class.py -q` |
| A2 | strip/smooth is claim-free + idempotent (FR-002a/b, SC-001a) | `pytest tests/unit/test_strip_smooth.py -q` |
| A3 | frozen subject_key lookup; transient failure never re-opens VERIFIED (FR-010/011, SC-003) | `pytest tests/unit/test_frozen_claim_cache.py -q` |
| A4 | value-independent fill/verdict cache key — PENDING vs VERIFIED phrasing collide (FR-012) | `pytest tests/unit/test_value_independent_cache_key.py -q` |
| A5 | durable placeholder round-trip — stored form keeps `{{claim:id}}`; `render_view` substitutes; no bake-in (FR-007/008, SC-007) | `pytest tests/unit/test_durable_placeholder.py -q` |
| A6 | planning skips low-level kinds — no fetch attempted, no `[UNRESOLVED-CLAIM:]` marker (FR-002/003) | `pytest tests/unit/test_planning_skip.py -q` |
| A7 | no-regression: existing claim/fill/grounding suites stay green (FR-014) | `pytest tests/unit/test_claim_* tests/unit/test_fill_* tests/unit/test_grounding_* tests/integration/test_claim_subject_reuse.py tests/integration/test_exact_count_no_regress.py -q` |

## B. Real-call paths (`LLMXIVE_REAL_TESTS=1` + free Dartmouth key)

| # | Scenario (spec) | Expected | Command |
|-|-|-|-|
| B1 | **Planning / skip** — a planning-stage doc asserts a wrong low-level number (US1 §1, SC-001) | number NOT fetched/grounded; NO marker; NO kickback; specific value replaced by a higher-level statement | `pytest tests/integration/test_planning_references_only.py::test_lowlevel_stripped -q` |
| B2 | **Planning / reference still gated** — same doc cites a fabricated DOI (US1 §3, SC-002) | reference flagged unresolvable; advancement blocked (fail-closed) | `pytest tests/integration/test_planning_references_only.py::test_fabricated_doi_blocks -q` |
| B3 | **Paper / verify + freeze** — the 9,988 OEIS exact count in a paper-stage doc (US2, SC-005) | verifies correctly AND freezes (subsequent lookup = no re-resolution) | `pytest tests/integration/test_paper_stage_freeze.py::test_exact_count_frozen -q` |
| B4 | **Determinism across rounds** — verify in round 1, rephrase in round 2..3 (US2 §1, SC-003) | same frozen value; zero re-resolutions; cache hit by subject_key | `pytest tests/integration/test_paper_stage_freeze.py::test_rephrase_no_waffle -q` |
| B5 | **Cross-run persistence** — re-run from a clean checkout (US2 §3, SC-004) | frozen value read from `state/claims/` with zero cold re-resolutions | `pytest tests/integration/test_paper_stage_freeze.py::test_cross_run_frozen -q` |
| B6 | **Paper / no-regress constants + entity facts** (SC-005) | pi≈3.14159, "capital of France = Paris" still verify | `pytest tests/integration/test_paper_stage_freeze.py::test_constants_and_entities -q` |
| B7 | **Planning / prevention** — generate a fresh planning doc (US3 §1) | Success Criteria / Technical Context carry reference anchors; the low-level detector finds zero non-citation claims (no pre-asserted specific values) | `pytest tests/integration/test_planning_doc_scope.py -q` |

## C. PROJ-552 regression (SC-006)

The concrete failure that motivated the spec: the wrong "49 prime knots at crossing 13" in a planning
doc must be stripped/generalized (not left, not blocked on), references must verify, and the stage
must advance without exhausting the kickback cap on that class of issue.

```bash
pytest tests/integration/test_proj552_planning_no_kickback.py -q
# Asserts: low-level count absent/generalized in the planning artifact; citations resolve;
#          convergence advances; kickback log contains no low-level-claim entry.
```

## D. Full pre-push gate (run before any commit to main)

```bash
python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider \
  --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs
ruff check .
mypy src/llmxive
```

All green + the real-call B/C scenarios passing = spec 020 satisfied. If any fix changes code,
**re-run the entire gate** (Principle: partial re-verification is not acceptable).

## Success-criteria → evidence map

| SC | Evidence |
|-|-|
| SC-001 / SC-001a | A2, A6, B1 |
| SC-002 | B2 |
| SC-003 | A3, B4 |
| SC-004 | B5 |
| SC-005 | A7, B3, B6 |
| SC-006 | C |
| SC-007 | A5 |
