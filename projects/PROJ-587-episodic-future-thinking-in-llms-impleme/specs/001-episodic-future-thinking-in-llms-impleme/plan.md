# Implementation Plan: Episodic Future Thinking in LLMs: Implementing Mental Time Travel

**Branch**: `001-episodic-future-thinking` | **Date**: 2026-06-01 | **Spec**: `specs/001-episodic-future-thinking/spec.md`
**Input**: Feature specification from `/specs/001-episodic-future-thinking/spec.md`

## Summary

This feature implements a neural episodic control module for Large Language Models (LLMs) to enable "mental time travel." The system stores planning trajectories as (state, action, outcome) tuples with semantic embeddings and retrieves them to construct future scenarios. The implementation targets a baseline transformer with a parameter count scaled to satisfy strict resource constraints (limited RAM, runtime within a reasonable timeframe)., augmented with a CPU-optimized vector index (FAISS HNSW). The plan validates whether episodic retrieval improves planning accuracy over standard transformers on ALFWorld and TextWorld benchmarks, while explicitly addressing methodological concerns regarding true episodic recollection vs. statistical pattern matching (WYSIATI bias) via counterfactual confidence calibration.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU build), `transformers` (4.40+), `faiss-cpu`, `scikit-learn`, `datasets`, `pandas`, `numpy`, `pytest`, `hydra-core`, `statsmodels`  
**Storage**: Local file system (parquet/jsonl) for datasets; FAISS index in memory for retrieval; `sqlite` for metadata logging.  
**Testing**: `pytest` (unit, integration), `pytest-cov` (coverage), manual statistical validation scripts.  
**Target Platform**: Linux (GitHub Actions Free Tier: limited CPU resources, 7GB RAM, no GPU).  
**Project Type**: Research Library / Benchmarking Suite.  
**Performance Goals**: Retrieval latency ≤ 500ms on CPU for ≥1000 entries; Full evaluation pipeline ≤ 6 hours.  
**Constraints**: No GPU/CUDA; No quantization requiring CUDA; Dataset size limited to fit available system memory; Model size capped at a lightweight parameter count suitable for resource-constrained environments.  
**Scale/Scope**: A held-out set of planning tasks; a substantial set of retrieval queries; A set of generated scenarios for coherence rating..

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Action |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | Plan mandates pinned `requirements.txt`, fixed random seeds, and fetching ALFWorld/TextWorld from specific official repository commit hashes recorded in `data/`. |
| **II. Verified Accuracy** | PASS | Plan includes a pre-commit hook invoking the `Reference-Validator Agent` to check all citations in `plan.md` before stage transition. |
| **III. Data Hygiene** | PASS | Plan includes checksumming of raw data downloads; no in-place modification; derivations written to new files. |
| **IV. Single Source of Truth** | PASS | All figures/stats in `paper/` must trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | PASS | Plan mandates a `update_state.py` script to update `updated_at` and content hashes in `state/projects/...yaml` upon any artifact change. |
| **VI. Computational Budget** | PASS | Architecture explicitly designed for small-scale parameter counts and CPU-only execution (FAISS-cpu, no CUDA). |
| **VII. Statistical Power** | PASS | Plan includes power analysis justification (n=10 variants, ICC modeled, α=0.05, d=0.8) and FDR control for multiplicity. |

### Versioning Mechanism (Principle V)
To satisfy Constitution Principle V, the `utils/update_state.py` script will be executed after any artifact modification. This script:
1. Computes a SHA-256 hash of the modified file.
2. Updates the `artifact_hashes` map in `state/projects/PROJ-587-episodic-future-thinking-in-llms-impleme.yaml`.
3. Updates the `updated_at` timestamp in the same file.
This ensures the state file is always synchronized with the repository content.

### Pre-Commit Validation (Principle II)
A `pre-commit` hook is configured to run `python utils/reference_validator.py --file plan.md`. If any citation fails verification against the primary source, the commit is blocked, ensuring the plan itself meets the Verified Accuracy Gate.

### Test Traceability Matrix (Technical Context)
The following `pytest` suites map to specific User Stories (US) and Functional Requirements (FR):
- `tests/unit/test_episodic_memory.py`: Covers US-1, FR-001, FR-002.
- `tests/integration/test_planning_service.py`: Covers US-2, FR-003, FR-004.
- `tests/integration/test_validation_service.py`: Covers US-3, FR-005, FR-006.
- `tests/unit/test_stats.py`: Covers FR-008 (Bonferroni/FDR implementation).
- `tests/integration/test_retrieval_latency.py`: Covers FR-007 (CPU performance).

### Task Generation Process (Project Structure)
The transition from `planned` to `tasked` is automated via `scripts/generate_tasks.py`. This script parses `plan.md` phases and converts them into actionable tickets in `tasks.md`, ensuring no manual intervention is required to define the work breakdown structure.

## Project Structure

### Documentation (this feature)

```text
specs/001-episodic-future-thinking/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (Generated by scripts/generate_tasks.py)
```

### Source Code (repository root)

```text
projects/PROJ-587-episodic-future-thinking-in-llms-impleme/code/
├── data/
│   ├── raw/                  # Downloaded ALFWorld/TextWorld datasets
│   ├── processed/            # Preprocessed parquet/feather files
│   └── checksums.txt         # SHA256 hashes for raw data
├── models/
│   ├── baseline_transformer.py   # standard transformer with a moderate parameter count
│   ├── episodic_memory.py        # FAISS index + retrieval logic
│   └── augmented_llm.py          # Transformer + Episodic Control Module
├── services/
│   ├── retrieval_service.py      # Semantic search logic
│   ├── planning_service.py       # Scenario generation logic
│   └── evaluation_service.py     # Accuracy, coherence, confidence scoring
├── experiments/
│   ├── run_baseline.py           # Baseline inference
│   ├── run_episodic.py           # Episodic inference
│   └── sensitivity_analysis.py   # Threshold sweeping (FR-006)
├── validation/
│   ├── counterfactual_gen.py     # Perturbation for FR-005
│   └── confidence_calib.py       # Confidence scoring logic
├── utils/
│   ├── logging.py
│   ├── stats.py                  # Mixed-effects, power analysis, FDR
│   └── update_state.py           # Constitution V compliance script
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── requirements.txt
└── main.py

data/
├── alfworld/                     # Raw and processed ALFWorld data
├── textworld/                    # Raw and processed TextWorld data
└── logs/                         # Execution logs, fallback events
```

**Structure Decision**: The single-project structure is selected to minimize overhead and ensure all components (data, model, eval) reside in a single reproducible environment. The separation of `models/`, `services/`, and `experiments/` aligns with the need to isolate the episodic module logic from the baseline transformer and the evaluation protocols.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Episodic Memory Module** | Required to distinguish true episodic recollection from semantic retrieval (US-3, Kandel's critique). | A simple vector store without (state, action, outcome) tuple structure and confidence scoring would fail to model the "cellular alphabet" of learning or support counterfactual validation. |
| **Counterfactual Validation Protocol** | Required to measure WYSIATI bias and confidence calibration (US-3, Kahneman's critique). | Standard accuracy metrics alone cannot distinguish between "lucky" pattern completion and genuine episodic simulation; perturbation is necessary to test confidence on unknown details. |
| **Mixed-Effects Modeling** | Required to handle variance across task variants and participants (FR-004). | Simple t-tests would ignore the nested structure of tasks and fail to control for family-wise error rates across multiple variants (FR-008). |

