# Implementation Plan: llmXive follow-up: extending "APPO: Agentic Procedural Policy Optimization"

**Branch**: `001-llmxive-followup` | **Date**: 2026-07-04 | **Spec**: `specs/001-llmxive-followup/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-followup/spec.md`

## Summary

This feature implements a CPU-only validation pipeline to test the hypothesis that a "Static Branching Score" (derived from frozen LLM next-token entropy/KL divergence at semantic steps) correlates with a "Dynamic Branching Score" (derived from APPO Advantage values on online rollouts). The implementation covers three phases: (1) Static score generation on GSM8K/MATH traces using a frozen decoder-only model (e.g., Phi-2) in CPU mode; (2) Dynamic score generation on a subset of tasks using the APPO algorithm with Advantage estimation (A(s,a)) based on binary reward signals; and (3) Statistical alignment and correlation analysis (Pearson/Spearman + permutation tests) to validate the proxy metric. The solution strictly adheres to the 7 GB RAM and 6-hour runtime constraints of free-tier GitHub Actions runners, avoiding GPU dependencies and large-model training.

> **Spec Conflict Note**: The source `spec.md` FR-002 and FR-003 mandate "likelihood gains" and "DTW/edit distance" respectively. This plan implements the scientifically necessary revisions (Advantage values, semantic step alignment) as per panel feedback. A kickback is required to update `spec.md` to match these definitions.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-only), `datasets`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `torch` (CPU wheel), `huggingface_hub`, `cleanrl` (for APPO base)  
**Storage**: Local temporary files in `data/` (parquet/jsonl), checksummed via `data/` hygiene protocols.  
**Testing**: `pytest` with unit tests for score calculation logic and integration tests for the full pipeline (mocked for APPO rollout *only* in tests).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7 GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Static score pass < 30 mins; Dynamic generation < 4.5 hours; Analysis < 30 mins. Total < 6 hours.  
**Constraints**: No GPU/CUDA; no 8-bit quantization; memory < 7 GB peak; time < 6 hours; must handle log(0) via epsilon smoothing; must exclude failed rollouts.  
**Scale/Scope**: Static pass on ~ tasks (to account for dropouts and alignment noise); Dynamic pass on subset; Analysis on aligned valid tasks.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Notes |
|-----------|-------------------|-------|
| **I. Reproducibility** | **Compliant** | Plan mandates pinned seeds, `requirements.txt` at `code/`, and re-runnable scripts on fresh runners. |
| **II. Verified Accuracy** | **Compliant** | Plan requires citing only verified dataset IDs (e.g., `openai/gsm8k`, `cleanrl`) and standard libraries; no invented URLs. |
| **III. Data Hygiene** | **Compliant** | Plan mandates checksums for raw data in `data/`, no in-place modification, and PII scanning. |
| **IV. Single Source of Truth** | **Compliant** | All figures/stats in the final paper must trace to `data/` rows and `code/` blocks. |
| **V. Versioning Discipline** | **Compliant** | Plan includes content hashing for artifacts and timestamp updates in state YAML. |
| **VI. Static-Dynamic Correlation** | **Compliant** | The core plan (Phase 3) is explicitly designed to compute Pearson/Spearman and p-values to validate this principle using Advantage values derived from external rewards. |
| **VII. Resource-Constrained** | **Compliant** | Plan explicitly forbids GPU/CUDA, quantization, and large training runs; mandates CPU-only inference and streaming. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-followup/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── models/              # Data classes for ReasoningTrace, BranchingScore, CorrelationResult
├── services/
│   ├── static_scorer.py # KL divergence calculation (CPU-only)
│   ├── dynamic_scorer.py# APPO rollout wrapper (subset)
│   ├── step_parser.py   # Semantic Step Parser (regex-based)
│   └── analyzer.py      # Alignment, correlation, permutation tests
├── cli/
│   └── run_pipeline.py  # Entry point: static -> dynamic -> analyze
└── lib/
    └── utils.py         # Epsilon smoothing, memory monitoring, logging

tests/
├── contract/            # Schema validation tests
├── integration/         # End-to-end pipeline tests (mocked APPO if needed)
└── unit/                # Unit tests for score calculations

data/
├── raw/                 # Downloaded datasets (checksummed)
├── processed/           # Intermediate score files
└── results/             # Final correlation outputs
```

**Structure Decision**: Single project structure (`src/`, `tests/`, `data/`) selected to maintain simplicity for a research pipeline. No frontend/backend split required. The `cli/` entry point ensures reproducibility via a single command.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **N/A** | Constitution Check passed. | N/A |

## FR/SC Coverage Map

| ID | Coverage in Plan |
|----|------------------|
| **FR-001** (Static Score) | Phase 1: `static_scorer.py` implements KL divergence vs uniform top-5 at semantic steps (parsed by `step_parser.py`). |
| **FR-002** (Dynamic Score) | Phase 2: `dynamic_scorer.py` runs APPO (via CleanRL) on subset with **Advantage estimation (A(s,a))** derived from binary rewards, not likelihood gains. |
| **FR-003** (Alignment) | Phase 3: `analyzer.py` aligns **semantic step identifiers** (extracted via regex) between static and dynamic traces. Steps without matching identifiers are excluded from correlation. |
| **FR-004** (Correlation) | Phase 3: `analyzer.py` computes Pearson/Spearman. |
| **FR-005** (Permutation) | Phase 3: `analyzer.py` runs a sufficient number of iterations. **Explicit fallback**: If memory > 6.5 GB or time remaining < 30 mins, iterations reduce to a substantially lower count to ensure job completion (SC-003/SC-004). |
| **FR-006** (Resource Limits) | Phase 0 & 1: Memory monitoring wrapper; streaming data; timeout handlers. |
| **SC-001** (r > 0.7) | Phase 3: Threshold check in `analyzer.py`. |
| **SC-002** (p < 0.05) | Phase 3: Significance check in `analyzer.py`. |
| **SC-003** (Time < 5h) | Phase 0: Runtime estimation and chunking strategy. |
| **SC-004** (Mem < 7GB) | Phase 0: Memory profiling and chunking. |
| **SC-005** (Residuals) | Phase 3: Ljung-Box test implementation in `analyzer.py`. |

## Testing Strategy

- **Unit Tests**: Verify KL divergence calculation, epsilon smoothing, and Advantage estimation logic.
- **Integration Tests**: Run the full pipeline on a *mocked* APPO environment (pre-computed Advantage values) to verify data flow and schema compliance.
- **Research Run Constraint**: **Mocks are strictly forbidden in the research run.** The actual research execution (Phase 2) MUST use the real APPO implementation (CleanRL) on the dataset. If the real APPO run fails to complete within constraints, the job must fail (exit code 1) rather than fall back to mocks, ensuring validity per Constitution Principle VI.
