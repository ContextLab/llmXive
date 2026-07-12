# Implementation Plan: llmXive follow-up: extending "From Chatbot to Digital Colleague"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-12 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This feature implements a reproducible synthetic experimental environment to test the "Digital Colleague" hypothesis regarding the "tipping point" of retrieval noise in large skill libraries. The system generates a set of deterministic multi-step tasks and a configurable library of Python skills with controlled semantic overlap. An agent executes these tasks across varying library sizes (10, 30, 50, 100) to measure **Execution Fidelity** (runtime success) and retrieval precision. A "Safe Pruning" heuristic is applied to test performance recovery, with explicit logging of pruning risks to account for causal entanglement with retrieval noise. The implementation relies entirely on CPU-tractable methods (scikit-learn, sentence-transformers CPU) to ensure execution within GitHub Actions free-tier constraints (limited CPU and RAM resources, time limits).

**Methodological Correction**: The plan replaces the spec-mandated "Piecewise Linear Regression" (FR-005) with "Logistic Regression with a Quadratic Term" to statistically validly handle the discrete nature of the library size predictor (10, 30, 50, 100). This deviation is documented as a necessary correction for statistical soundness.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn`, `sentence-transformers` (CPU-only), `pandas`, `numpy`, `pytest`, `pyyaml`, `statsmodels`  
**Storage**: Local JSON files (`data/synthetic/`) and CSV logs (`data/results/`)  
**Testing**: `pytest` with contract validation against YAML schemas  
**Target Platform**: Linux (GitHub Actions Runner)  
**Project Type**: Computational Research / CLI Tool  
**Performance Goals**: Complete full experiment (500 tasks × 4 library sizes × 2 conditions) in < 4 hours on 2 vCPU.  
**Constraints**: No GPU usage; memory footprint < 6 GB during embedding calculation; deterministic random seeds.  
**Scale/Scope**: 500 synthetic tasks, 100 skills, 4 experimental configurations, 1 statistical model.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Verification Method |
|-----------|-------------------|---------------------|
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/generate_data.py` and `code/agent.py`. Dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **PASS** | No external citations in code logic; synthetic data is self-contained. Any paper references in `research.md` will be validated by the Reference-Validator Agent. |
| **III. Data Hygiene** | **PASS** | Raw generated data (`data/raw/`) will be checksummed. Derived metrics (`data/processed/`) will be new files. No PII generated. |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final paper will be generated via `code/analyze.py` reading `data/processed/`. No manual entry. |
| **V. Versioning Discipline** | **PASS** | Artifacts will be hashed; `state/` will be updated on changes. |
| **VI. Synthetic Environment Validity** | **PASS** | **Ground-Truth Independence Mechanism**: The data generation process uses **two distinct random seeds**. Seed A generates the skill embeddings and library structure. Seed B assigns the ground-truth solution paths (a small set of skill IDs) to tasks. This ensures the ground-truth path is statistically independent of the embedding space, preventing the agent from "guessing" the correct path based on retrieval proximity. Overlap metrics (cosine similarity) are calculated and logged. |
| **VII. Pruning Intervention Fidelity** | **PASS** | Pruning logic (every 10 tasks, usage=0, similarity < 0.70) is implemented with a "Safe Pruning" variant that logs "Pruning Risk" when a skill with high similarity to ground truth is removed. The analysis stratifies by this risk count to account for causal entanglement. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file (Phase 0/1 artifact defining the plan)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Defined in this phase to guide code generation)
    ├── task.schema.yaml
    ├── skill.schema.yaml
    └── experiment_log.schema.yaml
```

**Structure Decision**: Selected "Single project" structure. The research is self-contained within a single Python package. Separation of `generate`, `run`, and `analyze` into distinct scripts ensures modularity and reproducibility while keeping the codebase lightweight for CI execution. **Note**: The `contracts/` directory contains the schema definitions (YAML) created in this phase to serve as the source of truth for the data model and to validate the generated JSON/CSV outputs.

### Source Code (repository root)

```text
projects/PROJ-975-llmxive-follow-up-extending-from-chatbot/
├── data/
│   ├── raw/                 # Generated synthetic data (tasks.json, skills.json)
│   └── results/             # Experiment logs (logs.csv, metrics.json)
├── code/
│   ├── __init__.py
│   ├── generate_data.py     # FR-001, FR-002: Synthetic data generation
│   ├── agent.py             # FR-003, FR-004: Agent execution & pruning
│   ├── analyze.py           # FR-005 (Corrected), FR-006, FR-007: Statistical analysis
│   ├── utils.py             # Embedding helpers, similarity metrics
│   └── config.py            # Experiment parameters (seeds, library sizes)
├── tests/
│   ├── unit/
│   │   ├── test_generation.py
│   │   └── test_agent.py
│   └── contract/
│       └── test_schemas.py  # Validates JSON output against contracts/
├── requirements.txt         # Pinned dependencies
└── README.md
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is strictly bounded by the synthetic data generation and statistical analysis. | The proposed structure is minimal and sufficient for the experimental loop. |

## Metric Mapping & Data Flow

The plan explicitly maps all defined metrics to the output storage format to ensure no data loss or ambiguity:

1.  **Retrieval Precision**: Calculated as Jaccard similarity between retrieved set and ground truth. Stored in `experiment_log.csv` and `experiment_log.schema.yaml`.
2.  **Retrieval Diversity**: Calculated as inverse variance of cosine similarities. Stored in `experiment_log.csv` and `experiment_log.schema.yaml`.
3.  **Execution Fidelity (Primary Outcome)**: Binary flag indicating if the retrieved code executed successfully and matched the expected output. Stored in `experiment_log.csv` and `experiment_log.schema.yaml`.
4.  **Pruning Risk Count**: Integer count of high-risk skills pruned. Stored in `experiment_log.csv` and `experiment_log.schema.yaml`.
5.  **Latency/Token Usage**: Stored in `experiment_log.csv`.

This mapping ensures the `experiment_log.schema.yaml` contract fully covers the data model defined in `data-model.md` and the metrics required by the research methodology.