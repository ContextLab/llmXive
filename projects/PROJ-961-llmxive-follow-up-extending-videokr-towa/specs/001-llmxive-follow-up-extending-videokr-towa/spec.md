# Specification: Video Reasoning Threshold Analysis
**Project**: llmXive follow-up: extending "VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding"
**Version**: 1.1 (Corrected)
**Date**: 2023-10-27
**Status**: Active

## 1. Overview

This specification defines the requirements for analyzing the "reasoning cliff" in video question answering tasks. The goal is to determine if there is a statistically significant drop in accuracy as the complexity (measured by graph hop count) of the required reasoning increases.

## 2. User Stories

### US1: Data Ingestion and Structural Annotation
As a researcher, I want to download the VideoKR-SFT dataset and annotate each question with the exact shortest-path hop count from the ground-truth knowledge graph, so that I can stratify performance by reasoning complexity.

### US2: Accuracy Stratification and Threshold Detection
As a researcher, I want to calculate accuracy per hop-bin and detect a non-linear "reasoning cliff" using a Permutation Test, so that I can quantify the threshold where reasoning capability breaks down.

### US3: Sensitivity Analysis of Threshold Definition
As a researcher, I want to verify the robustness of the detected "cliff" by sweeping threshold definitions, so that I can ensure the finding is not an artifact of a specific binning choice.

## 3. Functional Requirements

### FR-001: Data Annotation
The system must ingest the VideoKR-SFT dataset and the associated Knowledge Graph.
- Output: `data/processed/annotated_videokr.csv`
- Columns: `id`, `question`, `answer`, `chain_length` (integer), `chain_bin` (categorical), `correctness`.

### FR-002: Binning Strategy
The system must generate a binned column `chain_bin` from `chain_length` for categorical analysis.
- Default bins: '1', '2', '3+'.
- Logic: Aggregate hop counts >= 3 into the '3+' category.

### FR-003: Stratified Accuracy
The system must calculate accuracy rates for each hop-bin (1-hop, 2-hop, 3+).
- Output: `data/processed/accuracy_binned.png` and summary table.
- Constraint: If a bin has <50 samples, the system must flag for bin merging or deferral (see T020a).

### FR-004: Threshold Detection (Permutation Test)
The system must detect the optimal "knot" (threshold hop count) where accuracy drops significantly.
- Methodology: Permutation Test (n=1000) for change-point detection.
- Grid Search: Iterate knot locations from 1 to 5.
- Correction: Apply Bonferroni correction for multiple comparisons.
- **Note**: This requirement explicitly overrides the initial LRT proposal. The Plan's "Complexity Tracking" table mandates the Permutation Test to avoid inflated Type I errors from data-driven knot selection.

### FR-005: Continuous Visualization
The system must generate a continuous plot of accuracy vs. hop count to visualize the trend without binning artifacts.
- Output: `data/processed/accuracy_vs_hop_raw.png`.
- Method: Scatter plot with LOESS smooth trend line.
- Output Data: `data/processed/accuracy_vs_hop_raw.csv`.

### FR-006: Runtime Measurement
The system must log the total end-to-end runtime of the pipeline.
- Output: `data/processed/runtime_log.json`.
- Constraint: Must explicitly compare against the CI limit and flag if exceeded.

### FR-007: [REMOVED] Generalized Additive Models (GAM)
**STATUS**: REMOVED.
**Reason**: The Plan's "Complexity Tracking" table explicitly rejects GAMs for this task due to statistical invalidity on discrete ordinal variables (hop counts). The Permutation Test (FR-004) is the approved methodology for non-linearity detection.
**Resolution**: This requirement is removed from the specification to resolve the contradiction with the Plan (Issue F001).

## 4. Data Model

### 4.1 Input Data
- **VideoKR-SFT**: A CSV/JSONL dataset of video questions, answers, and correctness labels.
- **Knowledge Graph**: A graph structure (nodes and edges) representing entities and relationships required for reasoning.

### 4.2 Annotated Output
- **CSV**: `data/processed/annotated_videokr.csv`
 - `id`: Unique identifier (string)
 - `question`: Question text (string)
 - `answer`: Ground truth answer (string)
 - `chain_length`: Shortest path hops (integer, 1, 2, 3...)
 - `chain_bin`: Binned category (string: '1', '2', '3+')
 - `correctness`: Binary correctness (boolean/float)

## 5. Success Criteria

### SC-001: Annotation Coverage
- Log total input records, unresolvable count, and annotated count.
- Output: `data/processed/annotation_coverage.json`.

### SC-002: Threshold Significance
- Explicitly compare calculated p-value against alpha=0.05.
- Output: `data/processed/threshold_results.json` with `is_significant` boolean and `conclusion` string.

### SC-003: Robustness Verification
- Verify if the "cliff" remains significant (p < 0.05) in >= 2 of 3 threshold definitions.
- Output: `data/processed/stability_metric.json` with `robustness_status` ('PASS'/'FAIL').

### SC-004: Runtime Compliance
- Measure total runtime and compare against CI limits.
- Output: `limit_exceeded` flag in `runtime_log.json`.

### SC-005: Memory Compliance
- Measure peak memory usage and compare against 7GB limit.
- Output: `limit_exceeded` flag in `memory_log.json`.

## 6. Methodology Notes

### 6.1 Change-Point Detection
The project uses a Permutation Test for change-point detection rather than a Likelihood Ratio Test (LRT) or Generalized Additive Models (GAM). This decision is based on the Plan's "Complexity Tracking" table, which highlights the risks of data-driven knot selection with LRT and the statistical invalidity of GAMs on discrete ordinal variables.

### 6.2 Handling Small Bins
If a bin (e.g., '3+') has fewer than 50 samples, the system will attempt to merge it with the adjacent bin. If the merged bin is still underpowered, the statistical test for that specific comparison will be deferred, and the reason will be logged. No synthetic data will be generated to fill gaps.

## 7. Revision History

| Version | Date | Author | Changes |
|:--- |:--- |:--- |:--- |
| 1.0 | 2023-10-20 | Research Team | Initial draft including FR-007 (GAM). |
| 1.1 | 2023-10-27 | Research Team | **Removed FR-007** to align with Plan's Complexity Tracking table (Resolves F001). |