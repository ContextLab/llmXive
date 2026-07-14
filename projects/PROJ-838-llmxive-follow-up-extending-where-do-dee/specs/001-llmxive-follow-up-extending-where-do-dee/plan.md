# Implementation Plan: llmXive follow-up: extending "Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-12 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `specs/001-gene-regulation/spec.md`

## Summary

This feature implements a CPU-tractable pipeline to analyze deep-research agent trajectories from the TELBench dataset. The system parses early-stage semantic spans (first [deferred] of a trajectory) to construct a Claim-Dependency Directed Acyclic Graph (DAG) based solely on textual co-reference and citation logic. It then calculates normalized topological metrics (Global Connectivity) to predict trajectory collapse. The plan strictly adheres to the hypothesis that low structural connectivity in early reasoning predicts final failure, while ensuring all graph construction is independent of ground-truth error labels until the final validation phase.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `networkx`, `scikit-learn`, `spaCy`, `tqdm`, `pyyaml`, `requests`, `scipy` (no GPU/CUDA libraries).
**Storage**: Local filesystem (`data/raw`, `data/processed`), JSON/CSV/Parquet formats.
**Testing**: `pytest` (unit tests for graph construction, integration tests for pipeline flow).
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM).
**Project Type**: Research Data Pipeline / CLI Tool.
**Performance Goals**: Process 100 trajectories in < 30 minutes; full dataset within 6 hours.
**Constraints**: No GPU; strict memory limits (< 7 GB RAM); deterministic graph construction; no pre-labeled error data used in feature extraction.
**Scale/Scope**: Variable dataset size (TELBench); processing capped by CPU time limits.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Verification Strategy |
|-----------|--------|-----------------------|
| **I. Reproducibility** | PASS | `requirements.txt` pins versions; random seeds set in `code/`; dataset fetched from canonical HuggingFace URL; stratified split into training and testing subsets. |
| **II. Verified Accuracy** | PASS | Only HuggingFace URLs from the `# Verified datasets` block will be cited in `research.md`. |
| **III. Data Hygiene** | PASS | Raw data downloaded to `data/raw` with checksums; derivations written to `data/processed` with new filenames. |
| **IV. Single Source of Truth** | PASS | All metrics derived programmatically; no hand-typed statistics in reports. |
| **V. Versioning Discipline** | PASS | `code/hasher.py` computes SHA-256 hashes of all artifacts and updates the state file automatically after each phase. |
| **VI. Topological Independence** | PASS | Graph construction logic (`code/graph_builder.py`) explicitly excludes ground-truth labels; labels only used in `code/evaluator.py`. |
| **VII. CPU-Tractability** | PASS | Algorithms use `networkx`, `spaCy` (CPU mode), and `scikit-learn`; no deep learning inference; data sampled/streamed to fit RAM. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-838-llmxive-follow-up-extending-where-do-dee/
├── code/
│ ├── __init__.py
│ ├── config.py # Hyperparameters (cutoff_depth, seed)
│ ├── downloader.py # TELBench dataset fetching
│ ├── graph_builder.py # Span parsing & DAG construction (FR-001, FR-002)
│ ├── metrics.py # Connectivity calculation (FR-003)
│ ├── evaluator.py # Thresholding & Confusion Matrix (FR-004, FR-005)
│ ├── hasher.py # Versioning & Hashing utility (Principle V)
│ └── main.py # Pipeline orchestrator
├── data/
│ ├── raw/ # Downloaded TELBench JSON/CSV
│ ├── processed/ # Graphs (JSON), Metrics (CSV)
│ └── checksums.txt # Integrity records
├── tests/
│ ├── unit/
│ │ ├── test_graph_builder.py
│ │ └── test_metrics.py
│ └── integration/
│ └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen. The pipeline is linear (Download -> Parse -> Graph -> Metrics -> Evaluate), making a modular CLI/Script approach more efficient than a complex web service or multi-repo setup. This minimizes overhead for the 6-hour runner constraint.

## Phases & FR/SC Mapping

### Phase 0: Data Acquisition & Validation
* **Goal**: Fetch TELBench dataset, verify integrity, and sample a subset for development.
* **FR Mapping**: FR-001 (Parse TELBench), FR-006 (CPU environment).
* **SC Mapping**: SC-003 (Efficiency check on sample).
* **Steps**:
 1. Implement `downloader.py` to fetch data from `.
 2. Implement checksum verification (Constitution Principle III).
 3. Validate JSON structure (handle malformed files per Edge Case 3).
 4. **Versioning**: Run `code/hasher.py` to record SHA-256 hashes of raw data and update the project state file (Constitution Principle V).

### Phase 1: Graph Construction Engine
* **Goal**: Extract early spans and build DAGs using deterministic NLP.
* **FR Mapping**: FR-001 (Filter first [deferred]%), FR-002 (DAG from co-reference/citation only).
* **SC Mapping**: SC-003 (Efficiency).
* **Steps**:
 1. Implement span extraction logic with `cutoff_depth` parameter.
 2. Implement co-reference/citation detection using `spaCy` (dependency parsing + pronoun resolution) and regex for explicit citations (e.g., "[1]").
 * *Note*: This replaces vague "regex" with a specific, CPU-tractable library (`spaCy` with `en_core_web_sm`).
 3. Construct `networkx.DiGraph`.
 4. Handle edge cases: < [deferred]% spans (use all), zero edges (connectivity = 0.0).
 5. **Construct Validity**: Save a sample of graphs and their inferred edges for manual spot-checking to estimate edge detection accuracy.

### Phase 2: Metric Calculation
* **Goal**: Compute normalized topological features.
* **FR Mapping**: FR-003 (Global Connectivity).
* **SC Mapping**: SC-003 (Efficiency).
* **Steps**:
 1. Implement `metrics.py` to calculate Global Connectivity (edge-to-possible-edge ratio) normalized by node count.
 2. **Collinearity Handling**: Instead of calculating both Branching Factor and Connectivity (which are linearly dependent), the plan will use **Global Connectivity** as the primary metric. If multivariate analysis is needed later, PCA will be applied to raw graph statistics.
 3. Output per-trajectory CSV.

### Phase 3: Prediction & Validation
* **Goal**: Apply threshold and evaluate against ground truth.
* **FR Mapping**: FR-004 (Optimal Threshold), FR-005 (Confusion Matrix), FR-007 (Baseline), FR-008 (Linear reasoning check).
* **SC Mapping**: SC-001 (Precision), SC-002 (Correlation/Significance), SC-004 (Sensitivity analysis).
* **Steps**:
 1. **Split Data**: Split the dataset into Train and Test sets using stratification by the `label` field to ensure class balance is preserved.
 2. **Threshold Selection**: Calculate the optimal decision boundary on the **Train** set by maximizing the F1-score (or Youden's J statistic) on the ROC curve. This replaces the arbitrary "20th percentile of success" heuristic to avoid circular logic.
 3. **Power Analysis**: Calculate the effect size (Cohen's d) from the training split and perform a post-hoc power analysis. If power < 0.8, flag the limitation in the report.
 4. **Apply Threshold**: Apply the optimal threshold to the **Test** set to generate predictions.
 5. **Evaluate**: Compute Precision, Recall, F1, and p-values (scipy.stats) comparing predicted vs. actual labels.
 6. **Null Hypothesis**: Perform a permutation test (shuffling labels a sufficient number of times) to establish a null distribution for the correlation coefficient. Ensure the observed correlation significantly exceeds the null (p < 0.05).
 7. **Sensitivity Analysis**: Sweep thresholds (representative small values) and percentiles (10, 20, 30). Report the full matrix of results. Select the "best" threshold based on the highest F1-score on the validation set, not arbitrarily.
 8. **Versioning**: Run `code/hasher.py` to record hashes of all processed metrics and reports.

## Risk Mitigation

* **Risk**: TELBench dataset format changes.
 * **Mitigation**: `downloader.py` includes strict schema validation; `graph_builder.py` logs specific missing fields rather than crashing.
* **Risk**: Graph construction too slow for 6-hour limit.
 * **Mitigation**: Use vectorized `pandas` operations; limit `spaCy` processing to local windows; stream data if necessary.
* **Risk**: No variance in early spans (all sparse).
 * **Mitigation**: FR-008 explicitly checks for linear reasoning; if all success cases are linear, the hypothesis is adjusted in the report (associational, not causal).
* **Risk**: Construct Validity of Edge Detection.
 * **Mitigation**: Manual spot-check of 50 graphs to estimate precision/recall of the `spaCy`-based edge inference. If accuracy is < 60%, the study will explicitly qualify the "Connectivity" metric as a "heuristic proxy" rather than a ground-truth structural measure.