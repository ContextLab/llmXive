# Specification: Evaluating the Impact of Code Generation on Code Smell Frequency

## Overview
This document defines the requirements for a study comparing code smell frequencies between human-written code and LLM-generated code. The study employs a **Balanced Blocked Design** to ensure statistical validity.

## Deviation Log
- **Sample Size Adjustment**: The original spec requested ≥1000 human samples and ≥50 LLM samples. Per `plan.md` and `methodology-f30244be`, this has been updated to a **Balanced Blocked Design** of 150 human samples and 150 LLM samples (3 per repo × 50 repos) to ensure repository-level matching and statistical power within resource constraints.
- **Statistical Method**: The original spec suggested Shapiro-Wilk followed by Mann-Whitney U or Welch's t-test. Per `plan.md` and `methodology-f30244be`, this has been updated to use a **Blocked Permutation Test** (stratified by repository) to properly handle the blocked experimental design and avoid pseudoreplication.
- **Feature Rejection**: FR-007 (Automated PR generation) has been REJECTED and replaced by the Balanced Blocked Design methodology.

## 1. Functional Requirements

### FR-001: Human Sample Collection
**Target**: Collect **150 human-written code samples** (3 per repository × 50 repositories).
**Criteria**:
- Repositories must be public, have ≥100 stars, and ≥5 years of history.
- Samples must be "fresh" functions (introduced in a single commit, no prior history).
- Languages: Python and Java.

### FR-002: LLM Sample Generation
**Target**: Generate **150 LLM-generated code samples** (3 per task × 50 tasks).
**Criteria**:
- Tasks derived from the same Issue/PR descriptions used for human samples.
- Generated using HuggingFace Inference API (or equivalent) with strict timeout/backoff.
- Languages: Python and Java.

### FR-003: Static Analysis
**Target**: Run PMD CLI on all valid samples.
**Criteria**:
- Analyze for 4 specific smells: Long Method, Duplicated Code, Feature Envy, Long Parameter List.
- Enforce per-file timeout (2 min) and memory limit (2 GB).

### FR-004: Data Validation
**Target**: Verify syntax validity of ≥95% of samples.
**Criteria**:
- Generate `data/intermediate/validation_report.json`.
- Exclude invalid samples from analysis.

### FR-005: Statistical Analysis
**Target**: Compare smell frequencies using a **Blocked Permutation Test**.
**Criteria**:
- Stratification: Repository ID.
- Correction: Bonferroni for family-wise error rate (α ≤ 0.05).
- Effect Size: Cohen's d (or permutation equivalent).

### FR-006: Reporting
**Target**: Generate `reports/final_study_report.md`.
**Criteria**:
- Include statistical tables, effect sizes, and box plots.
- Use associational language only (no causal claims).
- Explicitly state the observational nature of the study.

### FR-007: [REJECTED] Automated PR Generation
**Rationale**: Replaced by Balanced Blocked Design to avoid statistical artifacts and ensure repository-level matching.

## 2. Statistical Comparison (SC)

### SC-001: Total Sample Size
**Target**: **300 total samples** (150 human + 150 LLM).
**Rationale**: Ensures balanced design across 50 repositories (3 samples per source per repo).

### SC-002: Statistical Test
**Method**: **Blocked Permutation Test** (stratified by repository).
**Rationale**:
- Accounts for repository-level variance (blocking factor).
- Non-parametric; robust to non-normality and zero-inflation.
- Avoids assumptions required by t-tests or Mann-Whitney U in blocked designs.

### SC-003: Threshold Sensitivity
**Target**: Sweep "Long Method" thresholds ∈ {100, 150, 200} lines.
**Rationale**: Verify robustness of results against arbitrary threshold choices.

## 3. User Stories

### US-1: Data Collection
**As a** researcher, **I want** to collect 150 human and 150 LLM code samples from 50 matched repositories, **so that** I have a balanced dataset for statistical comparison.
**Acceptance Criteria**:
- `data/raw/human_samples` contains 150 valid files with metadata.
- `data/raw/llm_samples` contains 150 valid files with metadata.
- `data/raw/manifest.csv` links all samples to repository and issue IDs.

### US-2: Static Analysis
**As a** researcher, **I want** to run PMD on all samples to extract smell metrics, **so that** I can quantify code quality differences.
**Acceptance Criteria**:
- `data/intermediate/analysis_results.json` contains smell counts for all 4 categories.
- `data/intermediate/tool_validity_status.json` confirms false-positive rate ≤ 5%.

### US-3: Statistical Comparison
**As a** researcher, **I want** to compare smell frequencies using a **Blocked Permutation Test**, **so that** I can determine if LLM-generated code has significantly different smell profiles.
**Acceptance Criteria**:
- **Scenario 1**: The system runs a Blocked Permutation Test stratified by repository.
 - **Given** smell metrics for 300 samples grouped by repository.
 - **When** the analysis is executed.
 - **Then** the output includes p-values corrected via Bonferroni and effect sizes.
 - **Note**: This replaces the previous "Shapiro-Wilk → Mann-Whitney U" workflow. Reference `methodology-f30244be`.
- **Scenario 2**: The system generates a final report with associational language.
 - **Given** the statistical results.
 - **When** the report is generated.
 - **Then** the report explicitly states the study is observational and avoids causal claims.

## 4. Data Models

### CodeSample
- `source_type`: "human" | "llm"
- `repository_id`: string
- `issue_id`: string
- `task_id`: string
- `language`: "python" | "java"
- `file_path`: string
- `function_name`: string
- `is_fresh_commit`: boolean

### SmellMetric
- `sample_id`: string
- `smell_type`: "Long Method" | "Duplicated Code" | "Feature Envy" | "Long Parameter List"
- `count`: integer
- `threshold_used`: float (for continuous metrics)
- `continuous_metric_value`: float (e.g., cyclomatic complexity)

### StatResult
- `smell_type`: string
- `p_value`: float
- `effect_size`: float
- `confidence_interval`: tuple(float, float)
- `correction_method`: string (e.g., "Bonferroni")
- `test_method_used`: string (e.g., "Blocked Permutation Test")