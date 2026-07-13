# Implementation Plan: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

**Branch**: `001-llmxive-memory-optimization` | **Date**: 2026-07-13 | **Spec**: `spec.md`

## Summary

This project implements a CPU-tractable evaluation of "Graph Memory" reconstruction strategies for LLM agents. It establishes a "Full" active reconstruction baseline on the LoCoMo benchmark and compares it against "Lazy" and "Greedy" heuristics designed to reduce node visitation (computational cost) while maintaining reasoning accuracy. The implementation strictly adheres to the "Reproducible" and "Edge Constraints" principles, running entirely on CPU with quantized models (4-bit) and enforcing strict timeout/error handling to ensure pipeline robustness against disconnected graphs and timeouts.

**Critical Methodological Clarifications**:
1.  **Power Analysis**: The study design assumes a Minimum Detectable Effect Size (MDES) of Cohen's d=0.2 (medium effect), alpha=0.05, and beta=0.20. The fixed sample size provides [deferred] power for this effect size. The hypothesis that heuristics maintain accuracy within 2% of baseline is treated as an equivalence test (TOST) rather than a simple difference test, acknowledging that detecting a [deferred] delta with N=100 may be underpowered; confidence intervals will be reported to quantify uncertainty.
2.  **Correlation Reframing**: The analysis acknowledges that `nodes_visited` is a deterministic output of the chosen strategy (policy), not an independent variable. Therefore, the analysis does not test a "correlation between depth and accuracy" (which would be tautological). Instead, it performs **Effect Size Analysis** comparing accuracy distributions at discrete depth strata (binned by strategy) and calculates the **equivalence margin** of the heuristic policy. Specifically, we use **Point-Biserial correlation** or **Logistic Regression** to model the relationship between traversal depth and binary success probability.
3.  **Inflection Point Reframing**: The "inflection point" is defined as a **Policy Sensitivity Threshold**: the lowest evidence threshold (from the sweep {0.5, 0.7, 0.9}) where the heuristic's mean accuracy drops below 95% of the baseline. This is a hyperparameter limit, not an emergent property of the data.
4.  **Robustness Ground Truth**: For Synthetic Noisy Graphs, the ground truth remains the original LoCoMo answer. Accuracy measures the strategy's ability to ignore irrelevant edges (noise tolerance).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `llama-cpp-python` (CPU wheels, 4-bit quantization), `pandas`, `scikit-learn`, `networkx`, `numpy`, `tqdm`, `pyyaml`, `statsmodels` (for TOST).  
**Storage**: Local `data/` directory (parquet/csv), `data/processed/` for results. No external DB.  
**Testing**: `pytest` (unit tests for graph traversal logic, integration tests for pipeline robustness).  
**Target Platform**: GitHub Actions Free Tier (Linux, 2 vCPU, ~7GB RAM, No GPU).  
**Project Type**: Computational Research / Benchmarking Suite.  
**Performance Goals**: Complete full benchmark run within 6 hours; individual task timeout at 30 minutes; memory usage < 6GB.  
**Constraints**: NO GPU/CUDA; NO 8-bit/4-bit via `bitsandbytes` (requires CUDA); NO mocked inference (must use `llama-cpp-python`); NO unverified dataset URLs.  
**Scale/Scope**: ~100-200 tasks (LoCoMo subset); synthetic noisy graph generation for robustness checks.

> **Dataset Variable Fit Note**: The LoCoMo dataset provides multi-hop reasoning queries (Task) and context. The "Memory Graph" is *constructed* from this context during the "Full" baseline run (as per the MRAgent methodology). The "synthetic noisy graph dataset" mentioned in FR-007/Principle VII will be generated programmatically by injecting irrelevant edges into the constructed graphs to test robustness, as no external "noisy graph" source exists in the verified list.

## Constitution Check

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/config.py`. `requirements.txt` pins versions. Data fetched via verified URLs. |
| **II. Verified Accuracy** | **PASS** | LoCoMo ground truth used for accuracy. Citations limited to verified URLs in `research.md`. |
| **III. Data Hygiene** | **PASS** | Raw data checksummed in `state/`. Derived results (CSVs) written to new files. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | All stats in final report generated from `data/processed/*.csv` via `code/stats.py`. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Artifacts tracked via content hash in state YAML. |
| **VI. Computational Efficiency** | **PASS** | Uses `llama-cpp-python` with 4-bit quantization on CPU. No GPU calls. Timeout logic enforces 30m/task limit. |
| **VII. Graph Topology Robustness** | **PASS** | Explicit task (T024) to generate synthetic noisy graphs and run paired t-test/Wilcoxon against baseline. Explicit task (T020) for sensitivity sweep. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-memory-optimization/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── task.schema.yaml
│   └── result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-894-llmxive-follow-up-extending-memory-is-re/
├── code/
│   ├── __init__.py
│   ├── config.py          # Seeds, timeouts, model paths, thresholds
│   ├── data_loader.py     # Fetches LoCoMo, generates synthetic noisy graphs
│   ├── graph_builder.py   # Constructs memory graphs from context (Full strategy)
│   ├── traversal.py       # Implements Full, Lazy, Greedy strategies
│   ├── inference.py       # Wrapper for llama-cpp-python (4-bit CPU)
│   ├── runner.py          # Main loop: enforces timeouts, handles edge cases, proceeds to next task
│   ├── stats.py           # TOST, Wilcoxon, Effect Size, Sensitivity Threshold Analysis
│   └── report.py          # Generates final CSV/JSON reports
├── data/
│   ├── raw/               # LoCoMo CSV, Synthetic graphs (generated)
│   └── processed/         # Results CSVs, statistical reports, sensitivity_analysis_report.csv
├── tests/
│   ├── unit/              # Graph logic, timeout enforcement
│   └── integration/       # End-to-end pipeline on small subset
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure (`code/`) chosen to minimize overhead for a research benchmarking suite. Separation of concerns (loader, builder, traversal, stats) ensures modularity and testability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Noisy Graph Generation** | Required by Constitution Principle VII and FR-005 to test robustness against irrelevant edges. | Using only real LoCoMo data would fail the robustness check requirement; external "noisy" datasets are not in the verified list. |
| **Quantized CPU Inference (`llama-cpp-python`)** | Required by Constitution Principle VI to forbid mocked inference and ensure real latency/token logging on free-tier CI. | Mock inference would violate the "Real Inference" constraint; GPU-based methods (bitsandbytes) are incompatible with the CPU-only CI environment. |
| **Strict Timeout & "Proceed to Next" Logic** | Required by FR-007 and US-4 to prevent pipeline hanging on single task failures. | Simple crash-on-error would invalidate the entire experiment run if one task fails, violating data integrity requirements. |
| **Sensitivity Analysis Sweep** | Required by Spec Assumption to validate the "evidence threshold" parameter. | A single threshold run would not validate the robustness of the heuristic choice. |

## Implementation Phases

### Phase 0: Data Preparation & Robustness Setup
*   **T001**: Download LoCoMo benchmark subset from verified HuggingFace URL.
* **T002**: Generate Synthetic Noisy Graphs by injecting **[deferred] irrelevant edges** (specifically [deferred] of total edges) into LoCoMo-derived structures. **Ground Truth**: Original LoCoMo answers (accuracy measures noise tolerance).
*   **T003**: Validate graph connectivity and handle degenerate cases (0 edges).

### Phase 1: Core Inference & Traversal Implementation
*   **T004**: Implement "Full" active reconstruction algorithm (baseline).
*   **T005**: Implement "Lazy" and "Greedy" traversal heuristics. **Constraint**: Must use `llama-cpp-python` with 4-bit quantization (e.g., `Phi-3-mini-Q4_K_M`). **Metric**: Must log `token_count` and `latency_seconds`. **Constraint**: Mock inference is strictly prohibited; real inference with quantized models is required to satisfy Constitution Principle VI.
*   **T006**: Implement `runner.py` main loop. **Constraint**: Must enforce 30-minute hard timeout per task. **Success Criteria**: On timeout, log "TIMEOUT" status, **log the event**, and **proceed to the next task** without hanging or crashing the pipeline.

### Phase 2: Execution & Sensitivity Analysis
*   **T007**: Execute Baseline (Full) on LoCoMo subset. Output: `baseline_full_results.csv`.
*   **T008**: Execute Heuristics (Lazy, Greedy) on LoCoMo subset. Output: `heuristic_results.csv`.
*   **T009**: Execute Heuristics on Synthetic Noisy Graphs. Output: `noisy_graph_results.csv`.
*   **T020**: **Sensitivity Analysis Sweep**: Implement sensitivity analysis sweep for **Lazy heuristic evidence threshold** (values {0.5, 0.7, 0.9}) on LoCoMo and Noisy datasets. Output: `sensitivity_analysis_report.csv`. **Mandatory**: This sweep is required to validate the Spec's Assumption about threshold justification.

### Phase 3: Statistical Analysis & Reporting
*   **T024**: **Robustness Check**: Perform paired t-test/Wilcoxon on **`noisy_graph_results.csv`** (Heuristic vs. Baseline). Output: **`noisy_graph_stats.csv`**. **Mandatory**: This explicitly addresses FR-005 and Principle VII.
*   **T025**: Perform Equivalence Testing (TOST) on LoCoMo results (Heuristic vs. Baseline) with margin ±2%. Report effect size (Cohen's d) and the corresponding confidence interval. Also perform TOST on `noisy_graph_results.csv` to verify robustness.
*   **T027**: **Threshold Detection**: Analyze `sensitivity_analysis_report.csv` to identify the **Policy Sensitivity Threshold**: the lowest threshold where mean accuracy < 0.95 * baseline_accuracy. **Mandatory**: Identify the specific complexity threshold where accuracy drops below **95% of the baseline**. Output: `threshold_analysis.json`.
*   **T028**: Generate final `results_summary.md` and `statistical_report.json`.

## Statistical Analysis Plan (Revised)

1.  **Hypothesis Testing**:
    *   **Primary**: Two One-Sided Tests (TOST) for equivalence. Null: Difference > 2% (non-equivalent). Alternative: Difference ≤ 2% (equivalent). Margin: ±0.02.
    *   **Secondary**: Paired t-test (or Wilcoxon) to measure effect size magnitude (Cohen's d) between Heuristic and Baseline.
    *   **Multiplicity Correction**: Benjamini-Hochberg procedure applied to the family of all pairwise comparisons (Lazy vs Full, Greedy vs Full) across all sensitivity thresholds and noise levels.

2.  **Power & MDES**:
    *   **Assumed MDES**: Cohen's d = 0.2 (medium effect).
    *   **Alpha**: 0.05. **Beta**: 0.20 ([deferred] power).
    *   **Limitation**: With N~100-200, the study is powered for d=0.2. Detecting a [deferred] delta (d~0.1) may be underpowered; confidence intervals will be reported to reflect this uncertainty.

3.  **Correlation/Association**:
    *   **Reframed**: No Pearson correlation between `nodes_visited` and `accuracy` (deterministic artifact).
    *   **Analysis**: Use **Point-Biserial correlation** or **Logistic Regression** to model the relationship between traversal depth (continuous) and success probability (binary). Compare accuracy distributions across discrete depth strata (binned by strategy). Report Effect Size (Cohen's d) of the strategy policy on accuracy.

4.  **Threshold Detection**:
    *   **Definition**: "Policy Sensitivity Threshold" = Lowest evidence threshold (from sweep) where Mean Accuracy < 0.95 * Baseline Accuracy.
    *   **Method**: Binning tasks by strategy/threshold, calculating mean accuracy per bin, identifying the first bin violating the [deferred] condition.
