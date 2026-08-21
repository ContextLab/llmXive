# Research: Evaluating Code Generation Impact on Code Smell Frequency

**Project ID**: PROJ-514-evaluating-the-impact-of-code-generation
**Status**: Implementation Complete
**Last Updated**: 2023-10-27

## Executive Summary

This document outlines the implementation of the "Balanced Blocked Design" for evaluating the impact of code generation on code smell frequency. The study compares human-written code samples against LLM-generated samples across multiple repositories to ensure statistical validity and control for repository-level variance.

## Balanced Blocked Design Implementation

### Design Overview

The study employs a **Blocked Permutation Test** design where:
- **Blocks**: Repositories serve as the blocking variable.
- **Treatments**: Human-written code vs. LLM-generated code.
- **Matching**: For each repository, exactly 3 human samples and 3 LLM samples are collected from the same issue/task context.

### Sample Size & Deviation Log

**Original Aspirational Target**: 1000 human samples / 50 LLM samples (per initial spec).

**Implemented Reality**: 150 total samples (50 repositories × 3 pairs per repository = 150 samples).

**Rationale**: The reduction from 1000+ to 150 samples was driven by:
1. **Statistical Power Analysis**: A balanced blocked design with 50 blocks (repositories) provides sufficient power (≥0.80) to detect medium effect sizes (Cohen's d ≥ 0.5) at α = 0.05, as verified in `specs/001-code-smell-comparison/spec.md` Section 4.3 (Deviation Log).
2. **CI/CD Constraints**: The 150-sample limit ensures the pipeline runs within standard CI memory (2GB) and time (2-hour) limits while maintaining reproducibility.
3. **Data Quality**: Prioritizing high-fidelity, verified samples over sheer volume reduces noise from low-quality or non-representative code.

> **Reference**: See `spec.md` Section 4.3 "Deviation Log" for the full justification of the sample size adjustment. This document summarizes the implementation state without duplicating the spec's deviation log.

### Data Collection Protocol

1. **Repository Selection**: Top 50 repositories by star count (descending), then name (ascending), filtered for:
 - Age ≥ 5 years (`created_at` < 5 years ago).
 - Minimum 3 distinct commits adding `.py` or `.java` files.
2. **Human Samples**: 3 distinct commits per repository, verified for "freshness" (no prior code smell context) via GitHub API diff context.
3. **LLM Samples**: 3 samples generated per human sample using the exact issue/task description, ensuring a 1:1 mapping to the blocked design.
4. **Traceability**: All samples include metadata sidecars with `commit_sha`, `issue_url`, `model_id`, and `prompt_hash` to satisfy Constitution Principles II (Verified Accuracy) and VI (Code Generation Transparency).

### Statistical Analysis Plan

- **Primary Test**: Blocked Permutation Test (stratified by repository) for each of the four code smell categories:
 - Long Method
 - Duplicated Code
 - Feature Envy
 - Long Parameter List
- **Correction**: Bonferroni correction applied across the 4 hypothesis tests (α ≤ 0.05 / 4).
- **Sensitivity Analysis**: Threshold sweeps for all four categories to assess robustness of findings.
- **Effect Size**: Cohen's d (or equivalent for permutation tests) reported with 95% confidence intervals.

### Implementation Status

| Component | Status | Artifact Path |
|-----------|--------|---------------|
| Directory Setup | ✅ Complete | `code/`, `data/`, `reports/` |
| Human Sample Collection | ✅ Complete | `code/01_data_collection/fetch_human_samples.py` |
| LLM Sample Generation | ✅ Complete | `code/01_data_collection/generate_llm_samples.py` |
| Static Analysis (PMD) | ✅ Complete | `code/02_static_analysis/run_pmd.py` |
| Statistical Engine | ✅ Complete | `code/03_statistical_analysis/compare_distributions.py` |
| Sensitivity Analysis | ✅ Complete | `code/03_statistical_analysis/sensitivity_analysis.py` |
| Final Report Generation | ✅ Complete | `code/04_reporting/generate_report.py` |

### Reproducibility & Hygiene

- **Seed Pinning**: `RANDOM_SEED` enforced via `code/utils/config.py` and validated by `code/utils/validate_seed_pinning.py`.
- **Data Integrity**: SHA-256 checksums recorded for all raw samples in `state/projects/PROJ-514-evaluating-the-impact-of-code-generation.yaml`.
- **Fail-Loud Loading**: No synthetic fallbacks; all data fetchers raise `DataFetchError` on failure (`code/utils/fail_loud_loader.py`).

## Conclusion

The implemented Balanced Blocked Design successfully addresses the research question while adhering to the constraints of CI environments and statistical validity requirements. The reduction to 150 samples is a deliberate, documented deviation that maintains scientific rigor. Future iterations may expand the sample size if compute resources allow, but the current design is sufficient for the MVP.