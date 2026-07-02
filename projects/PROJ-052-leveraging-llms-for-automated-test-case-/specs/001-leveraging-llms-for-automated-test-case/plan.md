# Implementation Plan: Leveraging LLMs for Automated Test Case Generation from Natural Language Requirements

**Branch**: `001-llm-test-generation` | **Date**: 2024-05-21 | **Spec**: `specs/001-llm-test-generation/spec.md`

## Summary
This project implements a pipeline to evaluate the capability of a quantized Phi large language model to generate executable JUnit tests from bug fix descriptions in the Defects4J dataset. The system extracts requirements, generates code, executes tests against target projects with JaCoCo instrumentation, and performs statistical analysis (Wilcoxon signed-rank as primary, t-test as sensitivity) to compare generated vs. manual coverage **on the specific lines changed by the bug fix**. The entire pipeline is constrained to run on GitHub Actions free-tier resources (CPU-only, ≤7GB RAM, ≤6h).

**Critical Methodological Note**: This study relies on a **strict pairing unit**: the specific manual test method(s) known to fail on the buggy version of the code. If Defects4J metadata does not isolate such a specific test for a given bug, that sample is **excluded** from the paired statistical analysis. The study proceeds with a descriptive analysis of the remaining paired subset, acknowledging that if the exclusion rate is high, the results are limited to the subset of bugs with isolated test cases.

**Statistical Interpretation Note**: The hypothesis range of 40-60% (SC-003) is treated as a **descriptive benchmark** for the mean ratio of coverage. Due to the likely small sample size (N) constrained by the 6-hour runtime limit, the study **cannot** guarantee sufficient statistical power to distinguish between specific values within this range (e.g., [deferred] vs [deferred]) or to reject a null hypothesis of zero difference with high confidence. Therefore, the primary output will be the **estimated effect size** and **95% confidence intervals**. The study will be explicitly framed as "exploratory" if the a priori power analysis indicates N is insufficient to detect a clinically meaningful effect size (e.g., d=0.5).

## Technical Context

**Language/Version**: Python 3.11 (orchestration), Java 17 (test execution), Bash (runner scripts)  
**Primary Dependencies**: `llama-cpp-python` (CPU inference), `pandas`, `scipy` (statistics), `jinja2` (prompting), `subprocess` (JaCoCo/Java execution), `pyyaml`, `jsonschema` (validation)  
**Storage**: Local filesystem (temporary build artifacts), Parquet files (input data)  
**Testing**: `pytest` (orchestration logic + **Schema Validation against `contracts/`**), Manual compilation checks (generated Java)  
**Target Platform**: GitHub Actions Free Tier (Ubuntu, 2 vCPU, ~7GB RAM)  
**Project Type**: Research Pipeline / CLI Tool  
**Performance Goals**: ≤6h total runtime for configured sample size; ≤30s timeout per test execution.  
**Constraints**: No GPU; Phi-2 model must be quantized (Q4_K_M or similar) to fit in 7GB RAM; JaCoCo must run on CPU.  
**Scale/Scope**: Configurable sample size (default small subset for CI feasibility); Defects4J projects limited to those with available bug descriptions in the verified dataset.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Random seeds pinned in `code/` for LLM inference (temperature=0, seed=42). External datasets fetched from verified HuggingFace URLs only. `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | **PASS** | **Gate:** The `Reference-Validator Agent` is invoked as a **blocking step** in the GitHub Actions workflow (`ci.yml`) before the `research_complete` stage. If any citation in `plan.md` or `research.md` is unreachable or mismatched, the CI job fails immediately. All dataset URLs in `research.md` are from the provided "Verified datasets" block. |
| **III. Data Hygiene** | **PASS** | Raw data (Parquet) downloaded to `data/` with checksums recorded. Derived data (coverage CSVs, stats) written to new files. No in-place modification. |
| **IV. Single Source of Truth** | **PASS** | Final report numbers will be generated programmatically from `data/coverage_metrics.csv` and `data/analysis_results.json`. No hand-typed values. |
| **V. Versioning Discipline** | **PASS** | Content hashes for data and code will be tracked in the project state YAML. |
| **VI. Deterministic LLM Generation** | **PASS** | Phi-2 inference configured with `seed=42`, `temperature=0.0`, `top_p=1.0` to ensure identical output for identical input. |
| **VII. Coverage Benchmarking** | **PASS** | JaCoCo will be used to measure coverage **on changed lines** for both generated and manual tests. Statistical tests (Wilcoxon primary, t-test sensitivity) implemented as per spec. |

## Project Structure

### Documentation (this feature)
```text
specs/001-llm-test-generation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── dataset.schema.yaml
    ├── coverage.schema.yaml
    ├── generated_test.schema.yaml
    └── analysis_result.schema.yaml
```

### Source Code (repository root)
```text
code/
├── __init__.py
├── config.py            # Configuration (sample limits, timeouts, model paths)
├── data_loader.py       # Loads Defects4J parquet, formats prompts, extracts changed lines
├── llm_generator.py     # Phi-2 inference wrapper (llama-cpp-python)
├── test_executor.py     # Compiles Java, runs JaCoCo (line-level), handles timeouts/retries
├── analyzer.py          # Statistics (Wilcoxon primary, t-test sensitivity, power analysis, effect size)
├── report_generator.py  # Creates final markdown/JSON reports
├── validate_schemas.py  # Validates data against contracts/ using jsonschema (called by pytest)
└── main.py              # Orchestration entry point
```

**Structure Decision**: Single project structure (`code/`) chosen to minimize overhead and simplify dependency management for a research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Line-Level JaCoCo Mapping** | Required to isolate coverage on *changed lines* only, ensuring a valid paired comparison (SC-001). | Comparing total project coverage is scientifically invalid as it mixes unrelated test suites. |
| **Statistical Rigor (Wilcoxon)** | Required by FR-005/FR-008/FR-010 to handle bounded, skewed coverage data. | Paired t-test on small, skewed samples violates assumptions and yields invalid p-values. |
| **Timeout/Retry Logic** | Required by FR-003 and FR-006 to handle infinite loops and transient failures. | Running without limits would cause CI jobs to hang and fail the 6-hour constraint. |
| **Strict Pairing & Exclusion** | Required to avoid comparing a single generated test against a global manual suite (Category Error). | Including unpaired samples would render the statistical difference meaningless. |
| **Power Analysis & Effect Size** | Required to address SC-003 limitations; p-values alone are insufficient for small N. | Reporting only p-values would lead to Type II errors and misinterpretation of "non-significant" results as "no effect". |

## Methodological Rigor & Statistical Plan

### 1. Pairing Unit Definition (Critical)
To address construct validity and the "Category Error":
- **Pairing Unit**: The specific set of code lines changed in the Defects4J bug fix commit **AND** the specific manual test method(s) known to fail on the buggy version.
- **Manual Baseline**: The coverage of the *specific* manual test method(s) on these changed lines.
- **Exclusion Rule**: If Defects4J metadata does not isolate a specific failing test method for a bug (i.e., only the full suite is provided), **that sample is excluded** from the paired statistical test.
- **Fallback**: Excluded samples are logged as "unpaired" and included only in descriptive statistics (e.g., generation success rate), but **not** in the paired coverage comparison. The study proceeds with the paired subset, acknowledging potential selection bias if the exclusion rate is high.

### 2. Statistical Test Selection & Power Considerations
- **Primary Test**: Wilcoxon signed-rank test. Coverage data is bounded [0, 100] and likely skewed. With small N (runtime constrained), normality assumptions for t-tests are unreliable.
- **Sensitivity Analysis**: Paired t-test. Only executed if Shapiro-Wilk p > 0.10 (stricter threshold) AND visual inspection confirms approximate normality.
- **Effect Size**: Cohen's d (for t-test) or Rank-biserial correlation (for Wilcoxon). **This is the primary metric of interest.**
- **Hypothesis Range (40-60%)**: Treated as a **descriptive target range**. The report will calculate the mean ratio and its 95% CI. 
- **Power Analysis**: 
 - **A Priori**: `analyzer.py` will calculate the required N to detect a specific effect size (e.g., d=0.5) with [deferred] power. This will be compared against the achievable N (runtime constrained).
  - **Post-hoc**: Reported **only as a descriptive limitation metric**. If N is insufficient, the study is explicitly framed as "exploratory". **Post-hoc power is NOT used to validate or justify the sample size.**
  - **Interpretation**: If the CI for the mean difference includes 0, or if the power is < 0.5, the conclusion will state "Insufficient evidence to claim LLM tests achieve comparable coverage," rather than "LLM tests do not achieve comparable coverage."

### 3. Quality Metrics (Assertion Density)
- **Assertion Density**: Calculated and reported as a **descriptive** metric to characterize test style. It is **NOT** used to validate "efficacy" or "quality" in the statistical conclusion, as it is a weak proxy for fault detection capability.

## Risk & Mitigation

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Invalid Pairing** | High (Scientific invalidity) | Strict line-level mapping. **Exclude** samples where specific manual baseline cannot be isolated. |
| **High Exclusion Rate** | Medium (Sample size reduction) | Monitor exclusion rate. If >50%, explicitly flag the study as limited to a specific subset of bugs in the final report. |
| **Low Power (Type II Error)** | High (Inconclusive results) | Perform a priori power analysis. If achievable N is low, explicitly label study as "exploratory" and focus on effect sizes/CI rather than p-values. |
| **Model Hallucination** | Medium (Invalid code) | Retry mechanism; mark as "failed to compile". |
| **Runtime Exceed** | High (CI failure) | Hard stop at 6h. Configurable sample limit. |

## Testing Strategy

- **Schema Validation**: The `pytest` suite (in `code/validate_schemas.py`) **MUST** assert that all generated data files (`coverage_metrics.csv`, `analysis_results.json`, etc.) strictly conform to the schemas defined in `contracts/` before any statistical analysis proceeds.
- **Compilation Checks**: Manual compilation checks for generated Java files are performed during execution.
- **CI Gate**: The `Reference-Validator Agent` is invoked in the CI workflow as a blocking gate before `research_complete`.