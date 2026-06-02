# Implementation Plan: Semantic Substantiation for the Claim-Fill Layer

**Branch**: `019-semantic-substantiation` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-semantic-substantiation/spec.md`

## Summary

Close the literal-presence residual: today a PROSE-channel numeric/entity fill is
accepted on bare token-presence anywhere in fetched text, so a coincidental match
(the "≤6 / Almoravid dynasty" failure) passes. The fix routes PROSE-channel
candidates through semantic substantiation while leaving STRUCTURED channels
(constants / OEIS / Wikidata — inherent subject↔value link) and the exact-count
literal gate untouched.

Technical approach: a single trust-boundary helper in `fill/extract.py`
(`_accept`) gates every candidate at the one place candidates are admitted
(`extract_value`, both the offline and LLM paths). For STRUCTURED channels it is
exactly today's `present_in_source`. For PROSE channels it additionally requires
(a) a deterministic, zero-network subject-keyword co-occurrence pre-filter, then
(b) a semantic `grounded` verdict from the existing
`grounding/entailment.py::assess`. A claim-kind pre-guard in `fill/service.py`
refuses bound/inequality and digit-less numeric claims before any fetch. Channel
STRUCTURED-vs-PROSE classification is a single source of truth in
`fill/channels/__init__.py` (unknown → PROSE, fail-closed). No change to
`conflict.choose`: failing PROSE candidates never enter the candidate list, so
the winner is structurally always a survivor and an all-fail set blocks via the
existing `[UNRESOLVED-CLAIM:]` marker.

## Technical Context

**Language/Version**: Python 3.11 (existing `src/llmxive` package)
**Primary Dependencies**: existing only — `grounding/entailment.assess`,
`grounding/service.number_substantiated`, `agents/grounding_guard`
(`_number_anchor_re`), `claims/canonical` (`_subject_keywords`, bound guards),
`backends/router.reasoning_chat`; PyYAML (already used by entailment). No new deps.
**Storage**: N/A (fill cache under `state/librarian-cache/` unchanged)
**Testing**: pytest — offline gate (`tests/unit`, `tests/contract`,
`tests/integration`) + real-call (`tests/real_call`, `LLMXIVE_REAL_TESTS=1` +
Dartmouth key, free models)
**Target Platform**: Linux/macOS CLI + GitHub Actions pipeline
**Project Type**: Single Python library/CLI (Option 1)
**Performance Goals**: the deterministic pre-filter rejects obvious coincidental
matches with zero network/LLM calls; `assess` (one reasoning call) runs only on
PROSE survivors — no extra LLM call for STRUCTURED or exact-count paths.
**Constraints**: fail-closed everywhere; zero regression on the 9988-exact-count,
π-constant, and Paris entity-fact paths; exact-count literal gate
(`number_substantiated`) byte-for-byte unchanged.
**Scale/Scope**: ~4 source files touched + 1 new gate module; ~6 new test files
(unit + real-call). No schema/migration changes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Single Source of Truth (NON-NEGOTIABLE)** — PASS. One channel classifier
  (`fill/channels`), one gate chokepoint (`_accept` in `extract.py`, called from
  both `extract_value` sites), reuse of `assess` and `_subject_keywords`
  unchanged. The plan explicitly REJECTS duplicating the gate into
  `conflict.choose`. The one private helper reused cross-module
  (`_subject_keywords`) is promoted to a public `subject_keywords` (single impl,
  public name) rather than copied.
- **II. Verified Accuracy (NON-NEGOTIABLE)** — PASS. This feature *is* the
  accuracy enforcement: a PROSE source must semantically assert subject↔value.
- **III. Real-World Testing** — PASS. The acceptance matrix is real-call against
  the live Dartmouth backend (Almoravid-negative, Paris-grounded,
  Sydney-contradicted); offline tests are the deterministic-layer secondary.
- **IV. Cost Effectiveness (Free-First)** — PASS. Free Dartmouth models only; the
  deterministic pre-filter avoids an LLM call on obvious coincidental matches.
- **V. Fail Fast** — PASS. Claim-kind pre-guard rejects bound/digit-less claims
  before any fetch; every gate is fail-closed (error/`not_found`/`contradicted`
  → reject).
- **VI. Convergent Review (NON-NEGOTIABLE)** — N/A to runtime behavior (governs
  the review pipeline, not this gate). Spec authored via the speckit flow.

No violations → Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/019-semantic-substantiation/
├── plan.md              # This file
├── research.md          # Phase 0 — design decisions (gate placement, classifier,
│                        #   doc shim, window, span reuse, FR-008 reconciliation)
├── data-model.md        # Phase 1 — entities (ChannelKind, gate contract, Verdict use)
├── quickstart.md        # Phase 1 — how to run the real-call acceptance matrix
├── contracts/
│   └── prose-gate.md     # Phase 1 — function contracts (classifier, _accept,
│                        #   prose_substantiated, subject_keywords)
└── tasks.md             # Phase 2 (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
src/llmxive/
├── fill/
│   ├── service.py            # fill_claim — ADD claim-kind pre-guard (bound/digit-less)
│   │                         #   before any fetch (after the existing kind guard)
│   ├── extract.py            # ADD _accept (single trust boundary) + prose gate call;
│   │                         #   route both extract_value gate sites through _accept
│   ├── relevance.py          # NEW — prose_substantiated: deterministic subject-keyword
│   │                         #   co-occurrence pre-filter + assess semantic gate + doc shim
│   ├── conflict.py           # UNCHANGED (documented: failing PROSE never reaches choose)
│   └── channels/__init__.py  # ADD STRUCTURED/PROSE single-source classifier
│                             #   (is_structured / is_prose; unknown → PROSE)
├── claims/
│   └── canonical.py          # promote _subject_keywords → public subject_keywords
│                             #   (single impl; update internal callers)
└── grounding/
    └── entailment.py         # REUSED UNCHANGED (assess, Verdict)

tests/
├── unit/
│   ├── test_fill_channels_kind.py     # NEW — classifier (structured/prose/unknown→prose)
│   ├── test_fill_relevance.py         # NEW — deterministic pre-filter (co-occur reject)
│   ├── test_fill_claimkind_preguard.py# NEW — bound/digit-less refused before fetch
│   └── test_fill_extract_gate.py      # EXTEND — _accept: structured pass-through,
│                                      #   prose reject without backend (fail-closed)
├── integration/
│   └── test_exact_count_no_regress.py # MUST STAY GREEN (STRUCTURED gate skipped)
└── real_call/
    └── test_semantic_substantiation.py# NEW — Almoravid-block, Paris-grounded,
                                       #   Sydney-contradicted, bound-preguard (live backend)
```

**Structure Decision**: Single-project Python library (Option 1). The new
behavior is a thin gate layer over existing, well-tested primitives; the only new
file is `fill/relevance.py` (the prose gate), keeping `extract.py` focused.

## Complexity Tracking

> No Constitution Check violations — section intentionally empty.
