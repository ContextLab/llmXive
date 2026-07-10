# Implementation Plan: Evaluating the Impact of Code Complexity on LLM Code Understanding

**Branch**: `001-evaluating-impact-of-code-complexity-on-llm-code-understanding` | **Date**: 2024-05-21 | **Spec**: `specs/001-evaluating-impact-of-code-complexity-on-llm-code-understanding/spec.md`
**Input**: Feature specification from `specs/001-evaluating-impact-of-code-complexity-on-llm-code-understanding/spec.md`

## Summary

This project evaluates the relationship between code complexity (Cyclomatic Complexity, Halstead Volume, Maintainability Index) and LLM code understanding performance using the `microsoft/Phi-3-mini-4k-instruct` model. The system downloads the CodeSearchNet Python subset (URL: `), annotates functions with complexity metrics using `radon`, executes LLM inference on three tasks (Summarization, Bug Detection, Code Completion), and performs statistical analysis (Spearman correlation, GLM with splines, PCA fallback) to test the hypothesis of a negative relationship for Phi-3. To ensure feasibility on GitHub Actions free-tier (2 CPU, 7 GB RAM), the plan utilizes `Phi-3-mini` instead of CodeLlama-7b and implements strict memory monitoring, stratified sampling to ensure high-complexity representation, and derived dataset generation for bug detection ground truth.

## Requirement Amendments

To align with Compute Feasibility constraints and Scientific Soundness requirements, the following amendments are formally recorded:

1. **FR-003 (Model)**: AMENDED. The spec requirement to use `codellama/CodeLlama-7b-Instruct-hf` is replaced with `microsoft/Phi-3-mini-4k-instruct` due to the 7 GB RAM limit on the free-tier runner. The research question is explicitly scoped to "Phi-3's performance" rather than general LLM performance.
2. **FR-003 (Tasks)**: NO CHANGE. All three tasks (Summarization, Bug Detection, Code Completion) remain required. The plan includes derived dataset generation steps (programmatic bug injection) to satisfy the ground truth requirements for Bug Detection and Code Completion.
3. **FR-004 (Metrics)**: AMENDED. Metrics for Bug Detection are defined as "substring match for injected bugs" (acknowledging construct validity limitations) rather than "natural bug detection".

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers` (CPU-only), `torch` (CPU), `radon`, `datasets`, `pandas`, `scikit-learn`, `statsmodels`, `evaluate`, `scipy`
**Storage**: Local file system (`data/raw/`, `data/processed/`, `results/`)
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions free-tier runner)
**Project Type**: Research pipeline / CLI
**Performance Goals**: Total runtime ≤ 6 hours, Peak RAM ≤ 7 GB
**Constraints**: No GPU, no 8-bit/4-bit quantization requiring CUDA, strict memory caps, deterministic reproducibility.
**Scale/Scope**: Stratified sample of CodeSearchNet Python (targeting high-complexity tail), 3 tasks, complexity metrics.
**Dataset Source**: `

> **Note on Model Selection**: The spec mentions `codellama/CodeLlamab-Instruct-hf`. However, loading a 7B parameter model in default precision on a 7 GB RAM runner exceeds memory limits (requires ~14 GB+). Per **Constitution VI** and **Compute Feasibility** rules, this plan substitutes `microsoft/Phi-mini-4k-instruct` (3.8B, CPU-tractable) as the primary inference engine. This is a formal amendment to FR-003.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Rationale |
|:--- |:--- |:--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/`; `radon` version pinned; external datasets fetched from canonical HuggingFace URLs. |
| **II. Verified Accuracy** | **PASS** | All dataset citations link to the "Verified datasets" block; no invented URLs. |
| **III. Data Hygiene** | **PASS** | Raw data preserved in `data/raw/`; checksums recorded; derivations written to new files in `data/processed/`. |
| **IV. Single Source of Truth** | **PASS** | All statistics derived from `results/` CSVs; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **PASS** | Content hashes tracked; artifact updates trigger state timestamp updates. |
| **VI. Computational Determinism** | **PASS** | `radon` configuration and version explicitly pinned; deterministic metrics for identical inputs. |
| **VII. Statistical Rigor** | **PASS** | **Binning Strategy (Low/Medium/High tertiles) explicitly defined in this plan document** (0-33rd, 34-66th, 67-100th percentiles) and implemented in `code/`. GLM with splines prioritized over binning for power. VIF > 5 triggers mandatory PCA fallback. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-impact-of-code-complexity-on-llm-code-understanding/
├── plan.md # This file
├── research.md # Phase 0 output
├── data-model.md # Phase 1 output
├── quickstart.md # Phase 1 output
├── contracts/ # Phase 1 output
└── tasks.md # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
code/
├── 01_data_acquisition.py # Downloads CodeSearchNet, extracts Python subset
├── 02_complexity_annotation.py # Computes Radon metrics, generates annotated CSV, handles bug injection
├── 03_inference_pipeline.py # Runs 3 tasks (Sum, Bug, Completion) with Phi-3
├── 04_metric_calculation.py # Calculates BLEU, ROUGE, Execution Pass, Bug Detection metrics
├── 05_statistical_analysis.py # Spearman, GLM (splines), Binning, Visualization, PCA
├── 06_report_generation.py # Generates final JSON/CSV report
├── utils/
│ ├── memory_guard.py # RAM monitoring and abort logic
│ ├── prompts.py # Task-specific prompt templates
│ └── binning.py # Binning logic and boundary recording
└── requirements.txt # Pinned dependencies

data/
├── raw/ # Original parquet files (checksummed)
└── processed/ # Annotated CSVs, filtered subsets, bug-injected versions

results/
├── inference_logs.jsonl # Raw LLM outputs
├── metrics.csv # Per-snippet performance metrics
├── binning_metadata.json # Record of tertile boundaries
└── analysis_report.json # Final statistical results
```

**Structure Decision**: Single `code/` directory with modular scripts. This ensures linear data flow (Acquisition → Annotation → Inference → Metrics → Analysis) and simplifies dependency management for the CI runner.

## Complexity Tracking (Feasibility Adaptations)

| Adaptation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Model Substitution (Phi-3 vs CodeLlama-7b) | CodeLlama-7b requires >14 GB RAM on CPU; runner limit is a fixed memory capacity. | Running CodeLlama-7b would cause immediate OOM failure on CI, preventing any results. |
| Task Scope (3 Tasks) | Spec FR-003 explicitly requires Summarization, Bug Detection, and Code Completion. | Reducing to 1 task would violate the spec's core research question regarding task-dependent complexity effects. |
| Derived Dataset (Bug Injection) | Raw CodeSearchNet lacks bug labels. | Synthetic bugs are a known limitation; no natural bug dataset fits the CodeSearchNet schema without external dependencies. |
| Stratified Sampling | Random sampling may miss the "High" complexity tail. | Ensures sufficient representation of high-complexity functions for correlation analysis. |
| PCA Fallback | Complexity metrics are highly collinear (r > 0.9). | Without PCA, GLM coefficients are uninterpretable; VIF > 5 triggers mandatory reduction. |

## Statistical Rigor Implementation

To satisfy **Constitution VII** and address panel concerns:

1. **Binning Strategy**: Complexity scores will be binned into **Low (lowest tertile)

The specific value to remove/generalize: 'lowest'

Rewritten passage:
Low (lowest tertile)**, **Medium (-66th)**, and **High (-100th)** tertiles. These thresholds are **defined in this plan** and implemented in `utils/binning.py`. Boundaries are recorded in `results/binning_metadata.json`.
2. **Continuous Analysis Priority**: GLM will use **splines** (natural cubic splines) to model non-linearity in the continuous domain. Binning is used only for descriptive visualization and robustness checks.
3. **Collinearity Handling**: Variance Inflation Factor (VIF) will be calculated. If **VIF > 5**, the plan mandates a **PCA fallback** to generate orthogonal complexity components before GLM fitting.
4. **Maintainability Index**: Due to its composite nature (often negative), Maintainability Index will be binned using **quantile-based** methods rather than fixed thresholds, and checked for distributional validity before inclusion.

## Data Flow & SC-005 Compliance

To satisfy **SC-005** (Validity of Inference):

1. **Denominator Tracking**: `01_data_acquisition.py` and `02_complexity_annotation.py` will log the count of `total_valid_snippets` (snippets passing syntax check and complexity calculation).
2. **Numerator Tracking**: `03_inference_pipeline.py` will log `successful_responses` (non-empty, non-error outputs).
3. **Metric Calculation**: SC-005 is measured as `successful_responses / total_valid_snippets`. The final report will explicitly state this ratio.
4. **Exclusion Logging**: Snippets excluded due to syntax errors or context limits are logged in `data/processed/exclusions.log` but **not** included in the denominator for SC-005.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Radon Parse Failure** | High | Snippets with syntax errors are logged and excluded. |
| **Context Window Exceeded** | Medium | Truncate code to a context-appropriate token limit.; log as "context_exceeded". |
| **Model OOM** | Critical | Memory guard script monitors RAM; reduces batch size to 1 or aborts. |
| **Bug Detection GT Missing** | High | Programmatic bug injection (random operator swap) for a subset of snippets; scope limited to "synthetic bug detection". |
| **High Complexity Tail Missing** | High | Stratified sampling ensures representation of high-complexity cases.. |
| **Collinearity** | High | VIF check with mandatory PCA fallback if VIF > 5. |