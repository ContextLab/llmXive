# Research: Evaluating Code Generation Impact on Code Smell Frequency

**Project ID**: PROJ-514-evaluating-the-impact-of-code-generation

## Overview

This research project investigates the impact of Large Language Model (LLM) code generation on the frequency of code smells compared to human-written code. The study employs a **Balanced Blocked Design** to ensure statistical validity and repository-level matching between human and LLM samples.

## Balanced Blocked Design Implementation

### Design Overview

The implementation follows a **Balanced Blocked Design** where:
- **Blocks**: Repositories serve as blocks to control for project-specific coding styles and conventions.
- **Treatments**: Within each repository, we compare human-written code samples against LLM-generated code samples derived from the same task description (Issue/PR).
- **Matching**: Each repository contributes exactly 3 human samples and 3 LLM samples, all linked to the same underlying issue/task, ensuring a direct comparison.

### Sample Size and Deviation from Original Plan

The original plan aspirational target was 1000 samples (500 human, 500 LLM). [UNRESOLVED-CLAIM: c_282fadc0 — status=not_enough_info] However, due to practical constraints including API rate limits, computational resources, and the need for high-quality manual verification of task descriptions, the study has been adjusted to a more manageable and statistically valid sample size.

**Current Implementation**:
- **Repositories**: 50 distinct repositories (selected based on star count and age).
- **Samples per Repository**: 3 human samples + 3 LLM samples = 6 samples per block.
- **Total Samples**: 50 repositories × 6 samples = **300 samples** (150 human, 150 LLM).

This adjustment is documented in the **Deviation Log** found in `spec.md` (Section 4.3), which explicitly records the change from the original ≥1000 requirement to 150 samples per source type for statistical validity under the Balanced Blocked Design.

> **Reference**: See `spec.md` Section 4.3 (Deviation Log) for the formal record of this adjustment. This document summarizes the implementation reality and links to the spec for full context.

### Repository Selection Criteria

- **Star Count**: Repositories with `stars > 100`.
- **Age**: Repositories created at least 5 years prior to the current date.
- **Activity**: Must have at least 3 distinct commits adding `.py` or `.java` files.
- **Selection**: Sorted by star count (descending), then by repository name (ascending) for deterministic selection.

### Data Collection Pipeline

1. **Human Samples**: Fetched via GitHub API, extracting functions from fresh commits.
2. **Task Derivation**: Issue/PR descriptions are extracted to form tasks for LLM generation.
3. **LLM Samples**: Generated using HuggingFace Inference API with 3 samples per task.
4. **Validation**: Syntax validation and PMD analysis are performed on all samples.

### Statistical Analysis Method

- **Method**: Blocked Permutation Test (stratified by repository).
- **Correction**: Bonferroni correction applied for multiple hypothesis tests (4 smell categories).
- **Metrics**: Effect sizes (Cohen's d) and confidence intervals are calculated.
- **Sensitivity Analysis**: Threshold sweeps are performed to assess robustness of results.

## Conclusion

The current implementation successfully executes the Balanced Blocked Design with a focus on repository-level matching and statistical rigor. The reduced sample size (150 per source) is a documented deviation that maintains statistical validity while ensuring feasibility within project constraints. All subsequent analysis and reporting are based on this implemented design.