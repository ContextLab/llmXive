# Implementation Plan: 001-gene-regulation (TELBench Topological Failure Prediction)

**Branch**: `001-gene-regulation` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-where-do-dee/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-where-do-dee/spec.md`

## Summary

This project implements a CPU-tractable pipeline to predict "collapse" in deep-research agent trajectories using topological metrics derived from early-stage reasoning spans. The approach parses the TELBench dataset (Hugging Face), constructs Claim-Dependency DAGs based solely on textual co-reference and citation logic (excluding ground-truth labels during construction), calculates normalized Average Branching Factor and Global Connectivity, and validates a data-driven threshold (optimized on a training split) against final trajectory labels in a held-out test set. The pipeline strictly adheres to the project constitution, ensuring reproducibility, data hygiene, and CPU-only execution within GitHub Actions constraints.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `pandas`, `networkx`, `datasets` (Hugging Face), `scikit-learn`, `tqdm`, `pyyaml`, `pytest`, `ruff`, `black`  
**Storage**: Local file system (`data/raw`, `data/processed`, `code/`)  
**Testing**: `pytest` (unit tests for graph construction, metric calculation, and threshold logic)  
**Target Platform**: Linux (GitHub Actions free-tier runner: multiple CPUs, ~7 GB RAM)  
**Project Type**: Data analysis pipeline / Research tool  
**Performance Goals**: Process 100 trajectories within 30 minutes; full dataset within 6 hours (streaming enabled).  
**Constraints**: CPU-only execution; no GPU dependencies; strict adherence to `cutoff_depth` logic; graceful handling of malformed JSON and short trajectories; all topological metrics must return 0.0 (not NaN) for degenerate graphs.  
**Scale/Scope**: Initial run on a sample of trajectories; full run on the complete TELBench dataset (size deferred to research phase, handled via streaming).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Mitigation |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | `requirements.txt` pins versions; `random.seed` set in `code/config.py`; dataset fetched from canonical Hugging Face URL; `data/` files checksummed. |
| **II. Verified Accuracy** | PASS | All dataset URLs cited from the `# Verified datasets` block in `research.md` (corrected to point to the actual dataset page/file); no external citations without verification. |
| **III. Data Hygiene** | PASS | Plan mandates checksumming of raw data; derivations written to new files (`data/processed/...`); no in-place modification. |
| **IV. Single Source of Truth** | PASS | All metrics trace to `data/processed/metrics.csv`; figures/stats in paper trace to this file. |
| **V. Versioning Discipline** | PASS | Artifacts will carry content hashes; state file updated on artifact changes. |
| **VI. Topological Independence** | PASS | Graph construction (FR-002) explicitly excludes error labels; labels applied only in validation phase (FR-005). Threshold derivation uses ONLY the training split's success class, NOT the test set, preventing circular reasoning. |
| **VII. CPU-Tractability** | PASS | Uses `networkx` and `pandas`; no deep learning frameworks; streaming strategy for large datasets. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-where-do-dee/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Pre-existing inputs for this review
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Configuration (cutoff_depth, paths, seeds)
├── downloader.py        # Fetches TELBench dataset
├── parser.py            # Parses JSON, extracts spans, builds DAGs
├── metrics.py           # Calculates Branching Factor, Connectivity, Linear Index
├── evaluator.py         # Threshold logic, prediction, confusion matrix, correlation
├── pipeline.py          # Orchestration script
└── utils.py             # Logging, error handling helpers

data/
├── raw/                 # Downloaded raw JSON (checksummed)
│   └── .gitkeep
└── processed/           # Intermediate artifacts
    ├── graphs/          # Saved DAGs (JSON)
    ├── metrics.csv      # Aggregated metrics
    ├── train_metrics.csv
    ├── test_metrics.csv
    └── .gitkeep

tests/
├── unit/
│   ├── test_parser.py
│   ├── test_metrics.py
│   └── test_evaluator.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schema_validation.py

requirements.txt
pyproject.toml           # Includes ruff/black config
```

**Structure Decision**: Single project structure chosen to minimize overhead for a data analysis pipeline. Separation of concerns (parser, metrics, evaluator) ensures testability and modularity. `data/` hierarchy enforces the "Raw vs. Processed" hygiene requirement.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | The current structure is minimal and sufficient for the scope. |

## Implementation Phases

### Phase 0: Data Acquisition & Verification
- **T001**: Verify dataset access (Hugging Face `NJU-LINK/TELBench`).
- **T002**: Download and checksum raw data to `data/raw/`.

### Phase 1: Graph Construction & Metric Calculation
- **T003**: Implement `parser.py` to extract spans and build DAGs (handling short trajectories and zero-edge cases).
- **T004**: Implement `metrics.py` to calculate Branching Factor, Global Connectivity, and Linear Reasoning Index (handling degenerate graphs with 0.0).
- **T005**: Save graphs to `data/processed/graphs/` and metrics to `data/processed/metrics.csv`.

### Phase 2: Statistical Validation & Threshold Justification
- **T006**: Split `metrics.csv` into `train_metrics.csv` and `test_metrics.csv`.
- **T007**: **Pilot Distribution Check**: Visualize success-class connectivity distribution and perform a Kolmogorov-Smirnov test to ensure a distinct mode exists before applying the 20th percentile cutoff.
- **T008**: **Power Analysis**: Report sample size and acknowledge power limitations if the dataset is small.

### Phase 3: Threshold Optimization & Prediction
- **T009**: **Threshold Optimization**: Sweep percentiles {10, 20, 30} on `train_metrics.csv` to select the threshold maximizing F1-score (replacing the fixed 20th percentile heuristic).
- **T010**: **Baseline Calculation**: Calculate and report `baseline_mean_connectivity_success` (FR-007).
- **T011**: **Linear Reasoning Analysis**: Calculate `linear_reasoning_index` and test for its presence in the success class (FR-008).
- **T012**: **Collinearity Handling**: Perform PCA or regularized logistic regression to address correlation between Branching and Connectivity.
- **T013**: **Correlation Test**: Calculate Spearman/Pearson correlation and p-value between connectivity and collapse (SC-002).
- **T014**: **Prediction**: Apply the optimized threshold to `test_metrics.csv` to predict collapse.

### Phase 4: Evaluation & Sensitivity Analysis
- **T015**: **Performance Metrics**: Calculate Precision, Recall, F1, and Confusion Matrix (FR-005).
- **T016**: **Sensitivity Analysis**: Sweep thresholds over the set {0.01, 0.05, 0.1} and percentiles {10, 20, 30} as per SC-004.
- **T017**: **Generate Report**: Compile all results into `evaluation_results.json`.

### Phase 5: Performance Verification
- **T018**: **Benchmark**: Run the pipeline on a representative set of trajectories and assert a predefined time limit. (FR-006).

## Risk Management

- **Dataset Access**: If TELBench is gated, the pipeline will fail explicitly. Mitigation: Fallback to public mirror if available.
- **Metric Instability**: Small graphs (< 5 nodes) may yield unstable metrics. Mitigation: Flag these as 'unstable' and exclude from threshold derivation or use bootstrap resampling.
- **Collinearity**: Branching and Connectivity are correlated. Mitigation: Use PCA or regularized regression.
- **Data Leakage**: Ensure threshold is derived ONLY from the training split. Mitigation: Explicit code separation in `evaluator.py`.