# Specification: Code Smell Comparison Study

## Version 1.2 (Updated per Plan & Methodology)

## 1. Introduction

This study investigates the association between code generation source (human-written vs. LLM-generated) and the frequency of specific code smells.

## 2. Functional Requirements

### FR-001: Human Sample Collection
**Target**: Collect exactly **150 human-written code samples**.
**Method**: Extract 3 "fresh" functions per repository from 50 selected public GitHub repositories (≥100 stars, ≥5 years history).
**Constraint**: Must use `git log --diff-filter=A` to identify commits introducing the functions.
**Output**: Files saved to `data/raw/human_samples/` with metadata JSON sidecars.

### FR-002: LLM Sample Generation
**Target**: Generate exactly **150 LLM-generated code samples**.
**Method**: Derive 50 tasks from the same Issue/PR descriptions used for human samples. Generate 3 samples per task using a programmatically accessible LLM API (e.g., HuggingFace Inference API).
**Constraint**: Must implement exponential backoff and timeout handling.
**Output**: Files saved to `data/raw/llm_samples/` with metadata JSON sidecars.

### FR-003: Data Validation
Ensure ≥95% of collected samples are syntactically valid (Python/Java).
Generate `data/intermediate/validation_report.json` listing excluded samples.

### FR-004: Static Analysis
Run PMD CLI on valid samples to detect 4 specific code smells:
1. Long Method
2. Duplicated Code
3. Feature Envy
4. Long Parameter List

### FR-005: Statistical Analysis
Perform a **Blocked Permutation Test** (stratified by repository) to compare smell frequencies.
Apply Bonferroni correction for family-wise error rate ≤ 0.05.

### FR-006: Reporting
Generate a final report (`reports/final_study_report.md`) including statistical tables, effect sizes, and box plots.
Language must be strictly associational (e.g., "associated with", "correlated with").

### FR-007: [REJECTED]
**Status**: REJECTED.
**Rationale**: Replaced by Balanced Blocked Design (FR-001/FR-002) to avoid statistical artifacts and ensure repository-level matching.

## 3. Statistical Constraints

### SC-001: Total Sample Size
**Target**: **300 total samples** (150 human + 150 LLM).
**Justification**: Based on the "Balanced Blocked Design" in `plan.md` and `methodology-f30244be`, which prioritizes repository-level matching over raw volume to ensure statistical validity in the presence of repository-specific noise.

### SC-002: Analysis Method
Use **Blocked Permutation Test** (stratified by repository) instead of standard parametric tests (Shapiro-Wilk → Mann-Whitney U or Welch's t-test) to account for the paired nature of the data (same repo, same task).

### SC-003: Correction
Apply Bonferroni correction for the 4 hypothesis tests performed (one per smell type).

## 4. Deviation Log

| Original Spec Requirement | Updated Requirement | Reason | Reference |
|:--- |:--- |:--- |:--- |
| FR-001: ≥1000 human samples | FR-001: 150 human samples (3 per repo × 50 repos) | Balanced Blocked Design ensures repository matching and statistical power within CI limits. | `plan.md`, `methodology-f30244be` |
| FR-002: ≥50 LLM samples | FR-002: 150 LLM samples (3 per repo × 50 repos) | Balanced Blocked Design ensures repository matching and statistical power within CI limits. | `plan.md`, `methodology-f30244be` |
| SC-001: 1050 total samples | SC-001: 300 total samples | Alignment with FR-001 and FR-002 targets. | `plan.md` |
| SC-002: Shapiro-Wilk → Mann-Whitney U | SC-002: Blocked Permutation Test | Paired data structure requires blocking by repository to control for confounding variables. | `methodology-f30244be` |

## 5. Data Model

### CodeSample
- `source_type`: "human" | "llm"
- `repository_id`: String (GitHub URL)
- `issue_id`: String (PR/Issue number)
- `task_id`: String (Unique task identifier)
- `language`: "python" | "java"
- `file_path`: String
- `function_name`: String
- `is_fresh_commit`: Boolean

### SmellMetric
- `sample_id`: String
- `smell_type`: String
- `count`: Integer
- `threshold_used`: Float
- `continuous_metric_value`: Float

### StatResult
- `smell_type`: String
- `p_value`: Float
- `effect_size`: Float
- `confidence_interval`: Tuple(Float, Float)
- `correction_method`: String
- `test_method_used`: String