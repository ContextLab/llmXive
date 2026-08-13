# Research: Evaluating Code Generation Impact on Code Smell Frequency

**Project ID**: PROJ-514-evaluating-the-impact-of-code-generation
**Status**: Active
**Last Updated**: 2024-05-21

## Overview

This research project investigates the statistical impact of Large Language Model (LLM) generated code on the frequency of specific code smells compared to human-written code. The study utilizes a **Balanced Blocked Design** to ensure repository-level matching and statistical validity.

## Methodology

### Balanced Blocked Design Implementation

The study employs a **Balanced Blocked Design** where code samples are grouped by their source repository (the "block"). This design controls for repository-specific coding styles, domain constraints, and complexity levels that might otherwise confound the comparison between human-written and LLM-generated code.

**Key Design Features**:
1. **Blocking Variable**: Repository ID (`repository_id` in `data/raw/manifest.csv`).
2. **Sample Allocation**: For each selected repository, we extract a matched set of samples:
 * **Human Samples**: Extracted from fresh commits adding `.py` or `.java` files (Task: `code/01_data_collection/fetch_human_samples.py`).
 * **LLM Samples**: Generated based on the same issue/PR descriptions associated with the human samples (Task: `code/01_data_collection/generate_llm_samples.py`).
3. **Statistical Test**: A **Blocked Permutation Test** is used for analysis (Task: `code/03_statistical_analysis/compare_distributions.py`), stratifying by repository to maintain the integrity of the blocked design. This avoids assumptions of independence that would be violated if repository-level effects were ignored.

### Deviation from Original Aspirational Targets

The original specification (see `spec.md`, **Section 4.3: Deviation Log**) initially proposed a target of 1,000 samples with a 50/50 split. However, practical constraints regarding API rate limits, computational resources for static analysis, and the complexity of the blocked design necessitated a revision.

**Current Implementation Reality**:
* **Total Target**: 150 samples (75 human, 75 LLM).
* **Repository Count**: 50 distinct repositories.
* **Samples per Repository**: 3 (1 human + 2 LLM variations, or 1.5 human + 1.5 LLM averaged, depending on the specific extraction logic in `fetch_human_samples.py`).
* **Rationale**: This reduction aligns with the deviation log in `spec.md` (Section 4.3), which explicitly updates the requirement to 150 samples to ensure statistical validity within the compute budget while maintaining the blocked design structure.

> **Reference**: For the full justification of this deviation, please refer to the **Deviation Log** in `spec.md`, Section 4.3. This document summarizes the implemented state rather than duplicating the spec's log.

### Data Sources

* **Human Code**: GitHub API (stars > 100, age > 5 years). Extracted via `code/01_data_collection/fetch_human_samples.py`.
* **LLM Code**: HuggingFace Inference API. Generated via `code/01_data_collection/generate_llm_samples.py`.
* **Static Analysis**: PMD CLI. Executed via `code/02_static_analysis/run_pmd.py`.

## Statistical Analysis Plan

1. **Primary Metric**: Frequency of four code smell categories (Long Method, Duplicated Code, Feature Envy, Long Parameter List).
2. **Test**: Blocked Permutation Test with Bonferroni correction (α ≤ 0.05 / 4).
3. **Sensitivity Analysis**: Threshold sweeps for all four smell categories to verify result stability (p-value variance < 0.01).
4. **Reporting**: Final report in `reports/final_study_report.md` using strictly associational language.

## Implementation Status

| Component | Status | Task ID |
|:--- |:--- |:--- |
| Project Structure | ✅ Complete | T001 |
| Data Collection (Human) | ✅ Complete | T012 |
| Data Collection (LLM) | ✅ Complete | T013 |
| Static Analysis (PMD) | ✅ Complete | T021 |
| Statistical Comparison | ✅ Complete | T027 |
| Sensitivity Analysis | ✅ Complete | T028 |
| Report Generation | ✅ Complete | T029 |

## Conclusion

This research pipeline successfully implements the **Balanced Blocked Design** to evaluate code smell frequencies. The current sample size of 150, as documented in the project's deviation log, provides a statistically valid basis for the blocked permutation test while adhering to resource constraints.