# Implementation Plan: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

**Branch**: `001-evaluating-robustness-llm-code` | **Date**: 2026-07-03 | **Spec**: `specs/001-evaluating-the-robustness-of-llm-generat/spec.md`

## Summary

This project evaluates the robustness of LLM-generated code against semantically-preserving input perturbations. The technical approach involves downloading the HumanEval dataset, generating perturbed variants (synonym substitution, typo injection, syntactic rephrasing), filtering them via a sentence-transformer similarity threshold (>0.95), executing code generation using a 4-bit quantized StarCoder2-3B model on CPU, and analyzing pass@1 degradation using Mixed-Effects Logistic Regression as the primary inferential engine.

**Critical Methodological Correction**: The plan explicitly deviates from the spec's FR-007 (aggregated McNemar test) which destroys task-level pairing. Instead, we implement a **Cochran-Mantel-Haenszel (CMH)** test for paired comparisons and prioritize **Mixed-Effects Logistic Regression** (FR-012) as the primary hypothesis test to account for task clustering.

The plan strictly adheres to CPU-first constraints (≤7GB RAM, ≤6h runtime) and uses only verified, open datasets.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `transformers`, `bitsandbytes`, `sentence-transformers`, `scikit-learn`, `statsmodels`, `pandas`, `numpy`  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `data/logs/`)  
**Testing**: `pytest` (unit tests for perturbation logic, integration tests for pipeline)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Complete full pipeline (164 tasks × perturbations) within **6 hours** (enforcing SC-003) on 2 vCPU, 7GB RAM. **This budget explicitly includes the time required for the fallback scenario to `starcoder2-1b` if the primary model triggers an OOM error.**  
**Constraints**: No local GPU; strict **30s timeout** for generation and execution (enforcing FR-005); -bit quantization mandatory for StarCoder2-3B.  
**Scale/Scope**: **164** HumanEval tasks; up to 3 perturbations per task (max **656** total samples); [deferred] coverage of original tasks (enforcing FR-011).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ | All random seeds pinned in `code/utils/seeds.py`; HumanEval fetched via `datasets` library; `requirements.txt` pins versions. |
| **II. Verified Accuracy** | ✅ | Citations in `research.md` restricted to verified URLs. **Mechanism**: Reference-Validator integrated as a **GitHub Action step that fails the job and blocks merge** on citation mismatch, satisfying the NON-NEGOTIABLE requirement. |
| **III. Data Hygiene** | ✅ | Raw data checksummed upon download; derived data written to new files; no in-place edits. |
| **IV. Single Source of Truth** | ✅ | All stats in paper trace to `data/processed/calibration_report.json`. **Mechanism**: Paper generation uses a **script that parses the JSON and rejects manual edits**; a CI step validates that paper text matches JSON values to prevent transcription errors. |
| **V. Versioning Discipline** | ✅ | Artifacts hashed; `state.yaml` updated on changes. |
| **VI. Secure Execution** | ✅ | Sandbox (subprocess with `timeout` + network disabled) used for code execution. |
| **VII. Perturbation Traceability** | ✅ | Perturbation type and raw similarity score logged for every candidate in `data/logs/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-evaluating-robustness-llm-code/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code

```text
code/
├── data/
│   ├── download.py          # HumanEval loader (verified source)
│   └── perturbation.py      # Synonym, Typo, Rephrase generators + similarity filter
├── model/
│   ├── inference.py         # StarCoder2-3B (4-bit CPU) + timeout enforcement + fallback
│   └── sandbox.py           # Code execution wrapper
├── analysis/
│   ├── statistics.py        # CMH, Mixed-Effects, Sensitivity
│   └── error_classifier.py  # Syntax/Logic/Hallucination tagging
├── utils/
│   ├── seeds.py             # Global seed management
│   └── logging.py           # Structured logging
├── main.py                  # Pipeline orchestrator
└── requirements.txt         # Pinned dependencies

data/
├── raw/
│   └── humaneval.parquet    # Downloaded dataset (checksummed)
├── processed/
│   ├── perturbation_candidates_raw.json   # All generated candidates
│   ├── perturbation_candidates_validated.json # >0.95 similarity
│   ├── inference_logs.json              # Pass/Fail results
│   └── calibration_report.json          # ECE/Robustness metrics
├── logs/
│   └── halt_report.json                 # Runtime/Resource logs
└── contracts/
    ├── error_classification_schema.yaml # Schema for error types
    ├── ... (other schemas)
```

**Structure Decision**: Single-project structure selected to minimize overhead for a research pipeline. All logic is modularized into `data`, `model`, and `analysis` packages to satisfy the "Single Source of Truth" and "Reproducibility" principles.

## Statistical Methodology

### Critical Methodological Correction
The spec's FR-007 mandates aggregating contingency tables, which destroys the paired nature of the data (164 tasks treated as one aggregate). This is methodologically invalid for McNemar's test.
**Plan Action**: We **do not** implement FR-007 as written.
1.  **Primary Test**: **Mixed-Effects Logistic Regression** (FR-012) is the primary inferential engine. It accounts for task-level clustering `(1 | TaskID)`.
2.  **Secondary/Descriptive**: **Cochran-Mantel-Haenszel (CMH)** test replaces the aggregated McNemar. CMH tests the association between perturbation and pass/fail while stratifying by `TaskID`, preserving the paired structure.

### Hypothesis Testing
-   **Primary**: Mixed-Effects Logistic Regression.
    -   Formula: `logit(P(pass)) = β0 + β1 * PerturbationType + (1 | TaskID)`
    -   Rationale: Accounts for non-independence of perturbations from the same task.
-   **Secondary**: Cochran-Mantel-Haenszel (CMH) Test.
    -   Rationale: Provides a stratified test of association (Original vs. Perturbed) controlling for task difficulty.

### Sensitivity Analysis
-   **Threshold Sweep**: Re-evaluate pass@1 rates for thresholds `{0.85, 0.90, 0.95, 0.99}`.
-   **Traceability**: This numeric sweep implements the spec's `{high, very high}` requirement (FR-009), mapping 0.95 to "high" and 0.99 to "very high".
-   **Purpose**: Quantify survivorship bias.

### Error Classification
-   **Method**: Rule-based + heuristic classification of execution failures.
-   **Sampling**: All failures if ≤ 50; stratified random sample of 50 if > 50.

### Statistical Implementation Details
The `code/analysis/statistics.py` module will implement the following distinct functions to ensure testability and modularity:
-   `calculate_pass_at1(results: List[Dict]) -> float`: Computes the pass@1 rate from a list of execution results.
-   `run_mcnemar_test(contingency: Dict) -> float`: Performs McNemar's test on a provided contingency table (for descriptive purposes).
-   `run_cochran_mantel_haenszel(results: List[Dict]) -> float`: Performs the CMH test on the full dataset, stratified by `TaskID`.
-   `run_mixed_effects_regression(results: List[Dict]) -> Dict`: Fits the Mixed-Effects Logistic Regression model and returns coefficients and variance components.
-   `perform_sensitivity_analysis(results: List[Dict], thresholds: List[float]) -> List[Dict]`: Re-evaluates pass rates across the specified threshold sweep.
-   `generate_calibration_report(results: Dict) -> None`: Aggregates all statistical outputs and writes the final `data/processed/calibration_report.json` file.

## Compute Feasibility & Constraints

-   **CPU-First**: All models (MiniLM-L6-v2, StarCoder2-3B-4bit) are selected specifically for CPU compatibility.
-   **Memory Budget**: StarCoderB (-bit) uses ~2.5GB RAM. MiniLM uses a compact memory footprint.. Remaining sufficient memory for Python overhead..
-   **Time Budget**: 164 tasks × 3 perturbations = A substantial number of inferences. With a timeout of several tens of seconds each, the theoretical maximum duration is on the order of several hours. Buffer included for data loading, analysis, and **fallback scenarios** (e.g., StarCoder2-1b if OOM). The 6-hour limit (SC-003) includes this buffer.
-   **Risk Mitigation**:
    -   **OOM**: If StarCoder2-3B-4bit OOMs, fallback to `starcoder2-1b` (1.5GB RAM) is triggered automatically. **The 6-hour budget explicitly accounts for the additional inference time of the fallback model.**
    -   **Timeout**: Hard 30s limit per generation; OOM/Timeout logged as "failure".

## Decision Rationale

1.  **Why HumanEval?** It is the only verified, open dataset with executable unit tests for code generation. Access-gated datasets (e.g., APPS) are excluded due to CI restrictions.
2.  **Why 4-bit Quantization?** Full precision StarCoder2-3B requires >10GB RAM, exceeding the runner limit. 4-bit is the only faithful CPU form available.
3.  **Why Mixed-Effects?** Perturbations of the same task are not independent. Ignoring this violates statistical assumptions.
4.  **Why CMH over Aggregated McNemar?** Aggregated McNemar assumes independence between tasks, which is false. CMH preserves the paired structure.
5.  **Why 30s Timeout?** Defined by US-2 acceptance criteria as the bounded limit for execution.
6.  **Why 656 Samples?** Defined by US-1 (up to 3 per task) × 164 tasks.

## Verification Strategy (Independent Test)

The 'Independent Test' for US-3 is updated to ensure data integrity:
1.  **Data Structure Check**: The pipeline must verify that `inference_logs.json` contains a `task_id` column and is in "long format" (one row per perturbation).
2.  **Pairing Check**: The statistical script must verify that for every `task_id`, there exists at least one 'original' and one 'perturbed' record before running the Mixed-Effects model.
3.  **Mock CSV Test**: A mock CSV is used to verify the *calculation logic* of the Mixed-Effects model, but the primary validation is the structural check of the real data pipeline.
4.  **File Existence Check**: The verification process confirms the existence of `data/processed/calibration_report.json` as the primary statistical output.