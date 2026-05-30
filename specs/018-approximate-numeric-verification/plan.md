# Implementation Plan: Per-Claim Verification Modes (Approximate-Numeric, Computational, Magnitude/Relational)

**Branch**: `018-approximate-numeric-verification` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/018-approximate-numeric-verification/spec.md`

## Summary

The verifier **selects a mode per claim**: **exact-count** (literal presence, spec-017, unchanged), **approximate-constant** (precision-aware rounding against a library-backed constants table or a fetched source), **computational** (safe `sympy` evaluation of self-contained arithmetic/comparison/%/unit/symbolic/logic claims — *no* source search), or **source-fact** (spec 016/017 search+ground). It also enables the two spec-017-deferred fill kinds (**magnitude/superlative**, **set/relational**). Mode selection is **hybrid** (deterministic heuristics → LLM tie-break only when ambiguous). Approximate tolerance is **round-to-stated-precision match** (hedge widens one place). The constants table is **library-backed** (`math` + `scipy.constants` CODATA, double precision). The computational result and the constants are **deterministic authorities** — never model memory; the evaluator computes, never the LLM. The exact-count path (the 9,988 scenario) MUST NOT regress.

## Technical Context

**Language/Version**: Python 3.11.
**Primary Dependencies**: existing `llmxive` — `claims/{classify,resolve,triple,models,pointer,service}.py`, `fill/{extract,service,conflict,citation_repair,models}.py` + `fill/channels/`, `grounding/service.number_substantiated`. NEW external: **`sympy`** (added to `pyproject.toml`, installed — the safe symbolic evaluator), `scipy.constants` (already a dep — CODATA), stdlib `math`/`ast`.
**Storage**: no new persistent stores — verification mode + computed/constant provenance ride on the existing `Claim.evidence` + spec-017 fill cache (`grounding/cache`).
**Testing**: `pytest` across `tests/{unit,contract,integration,real_call}`; offline gate `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`. Real-call gated by `LLMXIVE_REAL_TESTS=1`. The computational + constants + approximate-rounding paths are **deterministic** so most of their verification is offline (no network/LLM).
**Target Platform**: local pipeline runtime.
**Project Type**: single project (Python library + pipeline).
**Performance Goals**: constants + computation resolve with **zero network calls** (SC-003); deterministic and fast.
**Constraints**: **never `eval`/`exec`** — `sympy` parses/evaluates symbolically with restricted parsing; the **LLM never produces a computed/constant value** (FR-015/SC-010); the exact gate is untouched (FR-003); free-first (sympy/scipy free).
**Scale/Scope**: per-claim mode selection; 4 modes + 2 newly-enabled fill kinds.

## Constitution Check

*GATE: pass before Phase 0; re-check after Phase 1.*

| Principle | Assessment |
|-|-|
| **I. SSoT** (NON-NEGOTIABLE) | PASS — reuses spec-016/017 resolvers, triple logic, fill service/channels/conflict/citation-repair, present-in-source gate; new code is the mode selector + constants channel + approximate comparator + computational evaluator. The exact gate stays the single literal-match path (FR-003/FR-012). |
| **II. Verified Accuracy** (NON-NEGOTIABLE) | PASS — strengthens accuracy: approximate values judged by precision-aware comparison to a *sourced/library* true value; computational claims *evaluated* deterministically; nothing verified from model memory (FR-011). Any constant value entering code is verified against the library before use (FR-013). |
| **III. Real-World Testing** | PASS — real-call tests for the source-based parts; the deterministic modes (compute/constants/rounding) are exercised with real `sympy`/`scipy`/`math` (no mocks). |
| **IV. Free-First** | PASS — `sympy` + `scipy` are free/open-source; constants + computation need no paid service and no network. |
| **V. Fail Fast** | PASS — a computational claim the evaluator can't safely parse falls back/blocks (never guessed, FR-015); an approximate claim with no true-value source blocks. |
| **VI. Convergent Review** (NON-NEGOTIABLE) | PASS — unchanged: verified/filled claims advance; unresolved claims keep the spec-016 marker+gate. |

**Result: PASS — no violations. Complexity Tracking omitted.**

## Project Structure

### Documentation (this feature)

```text
specs/018-approximate-numeric-verification/
├── plan.md, research.md, data-model.md, quickstart.md
├── contracts/verification-modes.md
└── tasks.md   (/speckit-tasks)
```

### Source Code (repository root)

```text
src/llmxive/
├── verify/                          # NEW package — the per-claim verification modes
│   ├── __init__.py
│   ├── mode.py                      # hybrid mode selector: exact | approximate | computational | source (FR-001)
│   ├── approximate.py               # precision parsing + round-to-stated-precision comparison + hedge (FR-002)
│   ├── compute.py                   # safe sympy evaluator: arithmetic/comparison/%/units/symbolic/logic (FR-014/015)
│   └── constants.py                 # library-backed constants table: math + scipy.constants (CODATA) (FR-004/005)
├── fill/channels/constants.py       # NEW channel — wraps verify/constants as a FetchedSource (authoritative true value)
├── claims/resolve.py                # MODIFY — route numeric claims by mode (computational → compute; approximate → constants/approx gate); enable MAGNITUDE/RELATIONAL via _maybe_fill at triple NEI/REFUTED
├── claims/classify.py               # MODIFY (or sibling) — expose the numeric sub-triage hook used by verify/mode
├── claims/triple.py                 # REUSE resolve_superlative/resolve_relational (check-only) — fill added via resolve.py wire-in
├── fill/extract.py                  # MODIFY — present_in_source becomes mode-aware (approximate → round-to-precision vs source number)
├── fill/service.py                  # MODIFY — _FILLABLE_KINDS += {MAGNITUDE, RELATIONAL}; constants channel in dispatch
├── fill/channels/__init__.py        # MODIFY — channels_for routes MAGNITUDE/RELATIONAL + constants; AUTHORITY += constants
└── cli.py                           # MODIFY — enable the spec-018 modes on real runs (env setdefault)

tests/
├── unit/        test_verify_mode.py, test_verify_approximate.py, test_verify_compute.py, test_verify_constants.py, test_fill_constants_channel.py
├── integration/ test_verify_resolve_wireup.py (mode routing through resolve), test_fill_magnitude_relational_wireup.py
└── real_call/   test_verify_pi_e_real.py (constants, zero-network), test_compute_real.py (1+2=1, 1>2, units), test_fill_superlative_real.py (Saturn→Jupiter), test_fill_relational_real.py (Sydney→Canberra)
```

**Structure Decision**: a new `src/llmxive/verify/` package holds the four new mode components (selector, approximate comparator, computational evaluator, constants table); the constants table is also exposed as a fill **channel** (`fill/channels/constants.py`) so the approximate-fill path treats it as an authoritative source. Everything plugs into the existing `claims/resolve.py` dispatch + `fill/extract.present_in_source` gate + `fill/service` channel routing. The exact-count gate (`grounding.number_substantiated` / `number_appears_in`) is **not touched** (FR-003). Magnitude/relational reuse the spec-016 `triple.py` resolvers, with fill enabled by the existing spec-017 `_maybe_fill` helper.
