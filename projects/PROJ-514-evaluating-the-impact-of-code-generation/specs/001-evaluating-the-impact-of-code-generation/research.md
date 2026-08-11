# Research: Evaluating Code Generation Impact on Code Smell Frequency

## Project ID
PROJ-514-evaluating-the-impact-of-code-generation

## Overview
This research project investigates the association between code generation by Large Language Models (LLMs) and the frequency of code smells compared to human-written code. The study employs a **Balanced Blocked Design** to ensure statistical validity and repository-level matching.

## Design Implementation: Balanced Blocked Design

### Current Implementation Reality
The implemented study design utilizes a balanced allocation of samples to facilitate direct comparison and robust statistical analysis using blocked permutation tests.

- **Human-Written Samples**: 150 samples
- **LLM-Generated Samples**: 150 samples
- **Total Dataset**: 300 samples
- **Structure**: 50 repositories, with 3 samples per repository per source type (Human/LLM).

This design ensures that for every repository, we have a matched set of human and LLM code, controlling for repository-specific factors (e.g., coding style, project domain, existing codebase constraints).

### Deviation from Original Aspirational Design
The original research plan aspired to a 1000/50 split (1000 human samples vs. 50 LLM samples). However, this was revised to the current 150/150 balanced design.

- **Reason for Deviation**: The shift to a balanced design was driven by the need for statistical power in the blocked permutation test and to ensure fair comparison without the noise introduced by highly imbalanced groups.
- **Reference**: See the **Deviation Log** in `spec.md` (Section 4.3) for the full detailed rationale and the official record of this change. This document summarizes the *current* implemented state, while `spec.md` serves as the authoritative source for the change history.

## Methodology Summary

### Data Collection
- **Human Samples**: Retrieved from 50 public GitHub repositories (stars > 100, created < 2019-01-01). Functions were extracted from commits that added new Python or Java files.
- **LLM Samples**: Generated using the HuggingFace Inference API based on the exact issue descriptions and task requirements derived from the same GitHub repositories.
- **Matching**: Each LLM sample is paired with a human sample from the same repository and task context.

### Static Analysis
- **Tool**: PMD CLI with custom rulesets.
- **Metrics**: Long Method, Duplicated Code, Feature Envy, Long Parameter List.
- **Validity**: Tool validity is checked against a "clean" reference set to ensure false positive rates are within acceptable limits (< 5%).

### Statistical Analysis
- **Test**: Blocked Permutation Test (stratified by repository).
- **Correction**: Bonferroni correction applied for multiple hypothesis testing (4 smell categories).
- **Sensitivity**: Analysis performed on threshold variations for all four smell categories to ensure result stability.

## Data Hygiene & Traceability
- All sample files are checksummed (SHA-256) and logged in `state/projects/PROJ-514-evaluating-the-impact-of-code-generation.yaml`.
- API interactions and generation parameters are logged in `data/raw/api_logs.json`.
- Reproducibility is enforced via pinned random seeds and environment checks.

## Conclusion
The current implementation adheres to the **Balanced Blocked Design** as documented in the project's `spec.md`. This design provides a robust foundation for detecting statistically significant associations between code generation and code smell frequency, while controlling for repository-level confounders.