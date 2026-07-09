# Implementation Plan: Quantum Cognition in LLMs: Superposition States for Ambiguous Reasoning

**Branch**: `001-quantum-cognition-superposition` | **Date**: 2026-07-10 | **Spec**: `specs/001-quantum-cognition-superposition/spec.md`
**Input**: Feature specification from `/specs/001-quantum-cognition-superposition/spec.md`

## Summary

This feature implements a "quantum-inspired" adapter for the `bert-base-uncased` transformer to investigate whether complex-valued token representations (amplitude and phase) and Born-rule probability computation improve Word-in-Context (WiC) word-sense disambiguation compared to standard real-valued baselines. The approach maps frozen BERT hidden states to complex vectors, applies context-dependent phase shifts, performs vector addition (superposition), and derives probabilities via the interference cross-term (signed difference between squared magnitude of sum and sum of squared magnitudes), normalized by softmax. The plan includes rigorous baseline establishment, interference mechanism implementation, statistical significance testing via paired t-tests across multiple random seeds with bootstrap robustness checks, and an ablation study to isolate the interference cross-term. All implementation is constrained to CPU-only execution on free-tier CI (≤7 GB RAM, ≤6 hours).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `datasets`, `scikit-learn`, `numpy`  
**Storage**: Local `data/` directory (cached HuggingFace datasets), `code/` scripts  
**Testing**: `pytest` with parameterized seeds, contract validation via YAML schemas  
**Target Platform**: Linux (GitHub Actions free-tier runner, multiple CPU cores, sufficient RAM)  
**Project Type**: Computational research / ML experiment  
**Performance Goals**: Complete 5 paired runs (baseline + complex) + ablation + stats within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU/CUDA; no 8-bit quantization; frozen BERT weights; explicit error handling for NaN/Inf; strict adherence to complex arithmetic integrity.  
**Scale/Scope**: WiC dataset (SuperGLUE) size [deferred] (Assumptions: ≥ 500 examples); adapter parameter count < 1M.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Action/Note |
|-----------|-------------------|-------------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned random seeds in `code/`, canonical dataset fetching via `datasets` library, and isolated virtualenv. |
| **II. Verified Accuracy** | **PASS** | All citations (Busemeyer et al., WiC dataset) will be validated against primary sources. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan requires checksumming of downloaded datasets; raw data preserved; derivations written to new files. |
| **IV. Single Source of Truth** | **PASS** | Metrics trace to `data/` artifacts and `code/` execution blocks; no hand-typed stats in final paper. |
| **V. Versioning Discipline** | **PASS** | Artifact hashes tracked in state YAML; `updated_at` timestamps managed by Advancement-Evaluator. |
| **VI. Complex-Valued Representation Integrity** | **PASS** | Plan explicitly isolates adapter (trainable) from frozen BERT; mandates `torch.complex64`/`complex128` usage; enforces interference cross-term calculation. See `data-model.md` (Complex Token Representation) and `contracts/interference.schema.yaml`. |
| **VII. Statistical Significance of Interference Effects** | **PASS** | Plan mandates paired t-test (α=0.05) across 5 seeds + bootstrap resampling; requires reporting of p-value, t-statistic, Cohen's d, and 95% CI; null results reported with equal rigor. See `contracts/stats.schema.yaml` and `code/analysis/stats_test.py`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantum-cognition-superposition/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-594-quantum-cognition-in-llms-superposition/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── data/
│   │   └── download_wic.py          # Fetches WiC from SuperGLUE
│   ├── models/
│   │   ├── __init__.py
│   │   ├── bert_adapter.py          # Complex-valued adapter implementation
│   │   └── baseline_bert.py         # Frozen BERT baseline
│   ├── experiments/
│   │   ├── run_baseline.py          # US-1: Baseline evaluation
│   │   ├── run_quantum.py           # US-2: Complex model training & eval
│   │   ├── run_ablation.py          # FR-005: Classical sum-of-probs & Magnitude-Only
│   │   └── run_magnitude_control.py # New: Magnitude-only control condition
│   ├── analysis/
│   │   ├── stats_test.py            # US-3: Paired t-test, bootstrap CI, effect size
│   │   └── interference_check.py    # FR-010: Validate graded interference (outputs to contracts/interference.schema.yaml)
│   └── utils/
│       ├── complex_ops.py           # Complex arithmetic utilities
│       └── logging.py               # NaN/Inf detection
├── data/
│   └── raw/                         # Downloaded WiC (checksummed)
├── tests/
│   ├── unit/
│   │   └── test_complex_ops.py      # Synthetic interference tests
│   └── contract/
│       └── test_schemas.py          # Validate output against contracts
└── docs/
    └── paper/                       # Draft manuscript (post-research)
```

**Structure Decision**: Single project structure with modular separation of data, models, experiments, and analysis. This minimizes overhead for CI execution while maintaining clear boundaries for reproducibility (Constitution I, III) and complex-valued integrity (Constitution VI). The `experiments/` directory orders tasks: data download → baseline → quantum → ablation → stats, ensuring data availability before consumption.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Complex-valued arithmetic** | Core hypothesis requires phase interference; real-valued approximations cannot model destructive/constructive interference. | Classical vector addition (sum-of-probs) fails to capture cross-term negativity (FR-010, SC-005). |
| **Paired t-test + Bootstrap** | Required to distinguish signal from noise (US-3, SC-001); single-run comparison is statistically invalid. N=5 is a limitation, addressed by bootstrap CI. | Single-run comparison cannot establish significance (violates Constitution VII). |
| **Ablation Study (Classical + Magnitude-Only)** | Necessary to isolate interference contribution (FR-005, SC-002); without it, gains could be attributed to complex embeddings alone. | Omitting ablation conflates embedding complexity with interference mechanism. |

## Methodological Framework (Summary)

1.  **Baseline**: Frozen BERT on WiC (US-1).
2.  **Quantum Model**: Complex projection + Context-dependent Phase Shift (Unitary Rotation) + Superposition + **Signed Interference Cross-Term** (US-2).
3.  **Ablation**: Compare Quantum vs. Classical (Sum-of-Squares) vs. Magnitude-Only (No Phase Interaction) using shared representations (FR-005).
4.  **Validation**: Check for **graded** negative cross-term correlation with ambiguity (FR-010), not just binary negativity.
5.  **Stats**: Paired t-test (N=5) + k Bootstrap CI (US-3).

## Compute Feasibility

- **Hardware**: CPU-only (2 cores, 7 GB RAM).
- **Strategy**:
  - Frozen BERT (no gradient computation for transformer layers).
  - Compact adapter (< 1M parameters).
  - WiC dataset subset to [deferred] examples for training (Assumptions).
  - Batch size = 8 to fit memory.
  - Total runtime: ≤ 6 hours (5 seeds × 3 epochs + baseline + stats + bootstrap).
- **Libraries**: `torch` (CPU wheel), `transformers`, `datasets`, `scikit-learn`, `numpy` (all CPU-tractable).
- **Risk Mitigation**: If runtime exceeds a predefined threshold, reduce bootstrap iterations or sample multiple seeds for the full run.

## Limitations & Assumptions

- **Power Analysis**: N=5 is acknowledged as low power for d=0.5. Bootstrap CI is used to assess stability. Results will be interpreted with caution if CI includes zero.
- **Causal Claims**: All results framed as associational (FR-006); no random assignment of cognitive states.
- **Numerical Stability**: NaN/Inf detection and renormalization implemented (Edge Cases).
- **Dataset Fit**: WiC variables (token contexts, labels) are sufficient; no external cognitive measures needed (Assumptions).