# Implementation Plan: llmXive Follow-up: Trace Compressibility Analysis

**Branch**: `001-trace-compressibility` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-follow-up-extending-memslides-a/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-memslides-a/spec.md`

## Summary

This feature implements a computational research pipeline to determine which structural properties of multi-turn tool-execution traces (sequence entropy, tool-repetition frequency, argument semantic variance) predict their compressibility into symbolic rules without degrading persona-aligned agent behavior. 

The approach involves a strict two-stage design to ensure scientific validity and outcome variance:
1.  **Rule Induction**: Train a CPU-tractable rule-induction model (Decision Tree) on a **Training Set** of synthetic traces to reproduce final slide states.
2.  **Fidelity Measurement**: Apply the induced rules to a **Held-Out Test Set** of new revision requests. Measure the "Compressed Accuracy" (Edit Accuracy on new tasks) and compare it to the "Baseline Accuracy" (Raw Memory on new tasks).
    *   **Structural Diversity Strategy (Critical)**: The Held-Out Set is generated using a **distinct random seed** and a **deliberately perturbed distribution** (e.g., `variance_multiplier` = 1.5x for sequence length and tool repetition) compared to the Training Set. This ensures the outcome variable (fidelity loss = Baseline - Compressed) exhibits sufficient variance for correlation analysis, preventing a constant-zero result.
3.  **Correlation**: Use **Multiple Linear Regression** (per Constitution Principle VII) to correlate the structural metrics of the held-out traces with the resulting "Edit Accuracy difference".

This design ensures that the outcome variable (fidelity loss) is measured on unseen data with distinct structural properties, breaking the circular dependency where training data defines its own ground truth.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `scikit-learn` (DecisionTreeClassifier), `pandas`, `numpy`, `statsmodels` (for Multiple Linear Regression), `pytest`  
**Storage**: Local filesystem (`data/`), no external database. Data is streamed or loaded as needed.  
**Testing**: `pytest` (unit tests for metric extraction, integration tests for pipeline end-to-end), contract validation via YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7 GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete full pipeline (generation, extraction, training, evaluation, analysis) within 6 hours on CPU.  
**Constraints**: No GPU usage (CPU-first methodology); memory usage < 7 GB; no external API calls for data generation (synthetic only).  
**Scale/Scope**: Synthetic dataset of [deferred] sessions; held-out test set of [deferred] requests.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Plan Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/synthesis/generator.py` and `code/analysis/trainer.py`. All data generated via code, no external fetches. |
| **II. Verified Accuracy** | **Pass** | Citations (MemSlides, RuleFit) will be validated against primary sources. No fabricated URLs used (MemSlides has no verified URL, so synthetic generation is used). |
| **III. Data Hygiene** | **Pass** | All generated data in `data/raw/` will be checksummed. Derivations (metrics, models) written to new files in `data/processed/`. |
| **IV. Single Source of Truth** | **Pass** | All metrics and results in the final report will trace to specific rows in `data/processed/metrics.csv` and `data/processed/results.json`. **Feasibility Report** (T017) will be the source for SC-004. |
| **V. Versioning Discipline** | **Pass** | Content hashes for all artifacts in `data/` will be recorded in `state/...yaml`. |
| **VI. Trace Structural Integrity** | **Pass** | Generator will log exact tool sequences and argument variances to `data/raw/logs/trace_integrity.log`. T003 validates this log exists before metric extraction. |
| **VII. Latency-Accuracy Trade-off** | **Pass** | Evaluation script will isolate `Edit Accuracy` and `Retrieval Latency` and correlate with structural metrics via **Multiple Linear Regression** (strictly mandated by Principle VII). |

## Implementation Phases

### Phase 0: Data Generation & Validation
- **T000**: **External Validation Proxy**. Attempt to validate synthetic distribution against a small, verified proxy dataset (if available). Document outcome in `data/processed/validation_proxy.json`. If no proxy exists, document the limitation.
- **T001**: **Generate Synthetic Training Data**. Generate [deferred] multi-turn revision sessions for the Training Set using `seed=42`.
- **T002**: **Generate Synthetic Held-Out Data**. Generate [deferred] distinct sessions for the Held-Out Test Set.
    *   *Constraint*: Must use a **different random seed** (e.g., `seed=43`) and a **perturbed distribution** (e.g., `variance_multiplier` = 1.5 for sequence length and tool repetition) to ensure structural diversity and variance in the outcome variable (fidelity loss).
- **T003**: **Validate Trace Integrity**. Verify `data/raw/logs/trace_integrity.log` exists and contains valid structural metadata for all sessions. Fail pipeline if missing.

### Phase 1: Metric Extraction
- **T004**: **Extract Structural Metrics**. Compute sequence entropy, tool-repetition frequency, and argument semantic variance for all traces (Training and Held-Out). Output: `data/processed/metrics.csv`.

### Phase 2: Rule Induction & Fidelity Measurement
- **T005**: **Train Rule Induction Model**. Train Decision Tree on **Training Set** metrics to predict final slide state (or sequence of edits). Output: `data/processed/rules/model.json`.
    *   *Concurrency Note*: This task is the sole writer of the global model file.
- **T006**: **Evaluate Baseline Agent**. Run Raw Memory agent on **Held-Out Set**. Record `baseline_accuracy` and `baseline_latency` per request. Output: `data/processed/results/baseline_*.json`.
- **T007**: **Evaluate Compressed Agent**. Run Compressed Agent (using rules from T005) on **Held-Out Set**. Record `compressed_accuracy` and `compressed_latency` per request. Output: `data/processed/results/compressed_*.json`.
    *   *Concurrency Note*: Reads the immutable model from T005; writes to unique per-request files to avoid race conditions.
- **T008**: **Calculate Fidelity Loss**. Compute `accuracy_diff` = `baseline_accuracy` - `compressed_accuracy` for each trace in the Held-Out Set. Aggregate to `data/processed/results/summary.json`.

### Phase 3: Statistical Analysis
- **T016**: **Run Correlation Analysis**. Perform **Multiple Linear Regression** (per Constitution Principle VII) to correlate structural metrics (predictors) with `accuracy_diff` (outcome) using the **Held-Out Set**. Output: `data/processed/statistical_analysis_results.json`.
    - *Fallback*: If regression assumptions (linearity, normality) are violated, switch to Spearman Correlation and document in the report.
- **T015**: **Run Sensitivity Analysis**. Sweep the `compression_threshold` parameter (per FR-007).
    *   *Correction*: The sweep varies ONLY the `compression_threshold`. `compression_ratio` is a **derived outcome** reported for each threshold, not an independent variable. Output: `data/processed/sensitivity_report.json`.

### Phase 4: Feasibility & Reporting
- **T017**: **Feasibility Gate**. Measure total runtime, peak memory, and disk usage. Generate `data/processed/feasibility_report.json`.
    - *Gate*: If runtime > 6h or memory > 7GB, pipeline halts with failure status.
- **T018**: **Complete Final Report Generator**. Implement `code/evaluation/final_report_generator.py` to compile all artifacts into `data/processed/final_report.md`.
    *   *Implementation Detail*: The script must read `metrics.csv`, `summary.json`, `statistical_analysis_results.json`, `sensitivity_report.json`, and `feasibility_report.json`. It aggregates statistics, formats tables, and writes the complete markdown report to `data/processed/final_report.md`. This task ensures the final report is generated as a single, cohesive artifact.

## Project Structure

### Documentation (this feature)

```text
specs/001-trace-compressibility/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── trace.schema.yaml
    ├── metric.schema.yaml
    ├── result.schema.yaml
    ├── statistical_analysis.schema.yaml
    └── benchmark_results.schema.yaml
```

### Source Code (repository root)

```text
code/
├── synthesis/
│   ├── __init__.py
│   ├── generator.py          # FR-001: Synthetic trace generation
│   └── schema_defs.py        # MemSlides schema definitions
├── analysis/
│   ├── __init__.py
│   ├── metrics.py            # FR-002: Structural metric extraction
│   ├── rules.py              # FR-003: Rule induction (Decision Tree)
│   └── sensitivity.py        # FR-007: Sensitivity analysis
├── evaluation/
│   ├── __init__.py
│   ├── baseline_agent.py     # Raw memory agent implementation
│   ├── compressed_agent.py   # Symbolic rule bank agent
│   ├── benchmark.py          # FR-004, FR-005: Benchmarking
│   └── final_report_generator.py # FR-006, T018: Report compilation (IMPLEMENTED)
├── utils/
│   ├── logging.py
│   └── checksum.py
└── main.py                   # Pipeline orchestrator

data/
├── raw/                      # Generated synthetic traces
│   └── logs/                 # Trace integrity logs
├── processed/                # Metrics, models, results
│   └── feasibility_report.json # Output of T017
└── held_out/                 # Held-out test set

tests/
├── unit/
│   ├── test_metrics.py
│   └── test_synthesis.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py
```

**Structure Decision**: A modular CLI structure is selected to separate synthesis, analysis, and evaluation phases. This ensures data flows sequentially (Generation -> Metrics -> Training -> Evaluation), satisfying the compute feasibility constraint by avoiding concurrent writes to shared state.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The scope is strictly bounded by the spec. No unverified assumptions added. | N/A |