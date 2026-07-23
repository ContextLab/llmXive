# Metric Definitions for Robustness Evaluation

This document defines the statistical metrics and evaluation criteria used in the
"Evaluating the Robustness of LLM-Generated Code to Input Perturbations" study.
These definitions align with the functional requirements (FR-001 through FR-013)
and the experimental design outlined in `specs/001-evaluating-robustness-llm-code/`.

## 1. Pass@1

**Definition**: The proportion of tasks for which the model generates a correct
solution on the first attempt.

**Formula**:
```
Pass@1 = (Number of tasks passed on first attempt) / (Total number of tasks)
```

**Context**:
- Calculated separately for **original** (benign) prompts and **perturbed** prompts.
- A task is considered "passed" if the generated code executes successfully in the
 sandbox and satisfies all unit tests defined in the HumanEval dataset.
- Used as the primary dependent variable to measure the degradation in performance
 caused by input perturbations.

**Relevance**:
- **FR-001**: Establishes the baseline robustness metric.
- **US-3**: Provides the raw data for statistical significance testing (McNemar's).

---

## 2. McNemar's Test

**Definition**: A statistical test for paired nominal data used to determine if
there is a significant difference in the proportion of successes between two
related groups (original vs. perturbed prompts for the same task).

**Applicability**:
- Used when the same set of tasks is evaluated under both conditions (original
 and perturbed).
- The data is organized in a 2x2 contingency table:
 | | Perturbed Pass | Perturbed Fail |
 |---|---|---|
 | **Original Pass** | a | b |
 | **Original Fail** | c | d |
- Where:
 - `a`: Tasks passed by both original and perturbed.
 - `b`: Tasks passed by original but failed by perturbed.
 - `c`: Tasks failed by original but passed by perturbed.
 - `d`: Tasks failed by both.

**Formula**:
```
χ² = (|b - c| - 1)² / (b + c)
```
(With continuity correction, as implemented in `scipy.stats.mcnemar`).

**Interpretation**:
- A low p-value (typically < 0.05 after correction) indicates that the perturbation
 significantly altered the model's success rate.
- Specifically tests if the rate of `b` (Original Pass / Perturbed Fail) is
 significantly higher than `c` (Original Fail / Perturbed Pass), indicating
 degradation.

**Relevance**:
- **FR-004**: Requires statistical significance testing for performance differences.
- **US-3**: Implemented in `code/analysis/statistics.py` to aggregate results across
 perturbation types.

---

## 3. Bonferroni Correction

**Definition**: A method to counteract the problem of multiple comparisons (Type I
errors) when performing multiple statistical tests simultaneously.

**Context**:
- In this study, McNemar's test is performed separately for each perturbation type
 (e.g., `synonym`, `typo`, `rephrase`).
- Performing multiple tests increases the probability of finding a significant
 result by chance.

**Formula**:
```
α_corrected = α_original / n
```
Where:
- `α_original` is the desired significance level (typically 0.05).
- `n` is the number of comparisons (number of perturbation types).

**Implementation**:
- If `n = 3` (synonym, typo, rephrase) and `α = 0.05`, the corrected threshold is:
 `0.05 / 3 ≈ 0.0167`.
- A result is only considered statistically significant if its p-value is less
 than `α_corrected`.

**Relevance**:
- **FR-005**: Mandates correction for multiple comparisons to ensure rigor.
- **US-3**: Applied to the output of McNemar's tests in `code/analysis/statistics.py`.

---

## 4. Semantic Similarity Threshold

**Definition**: The minimum cosine similarity score required between the original
prompt and the perturbed prompt for the perturbation to be considered valid.

**Threshold**: **> 0.95**

**Measurement**:
- Calculated using the `sentence-transformers/all-MiniLM-L6-v2` model.
- The model encodes both the original and perturbed code strings into vectors.
- Cosine similarity is computed between these vectors.

**Constraint**:
- **FR-002**: Explicitly requires a high threshold to ensure semantic preservation.
- **FR-003**: Prohibits fallback to lower thresholds (e.g., 0.90) if the strict
 threshold is not met. If a candidate does not exceed 0.95, it is discarded.

**Relevance**:
- **US-1**: Drives the filtering logic in `code/data/semantic_validator.py`.
- Ensures that observed performance drops are due to surface-level perturbations,
 not changes in the underlying task logic.

---

## 5. Mixed-Effects Logistic Regression

**Definition**: A statistical model that extends logistic regression by including
both fixed effects (variables of primary interest, e.g., perturbation type) and
random effects (variables that introduce variability but are not the primary focus,
e.g., specific task difficulty).

**Model Structure**:
```
logit(P(Success)) = β₀ + β₁ * Perturbation_Type + u_task
```
Where:
- `β₀`: Intercept.
- `β₁`: Fixed effect coefficient for the perturbation type.
- `u_task`: Random intercept for each task (assumed to be normally distributed).

**Output**:
- **Fixed Effects**: Estimates the average impact of perturbation on success odds.
- **Variance Components**: Estimates the variance attributable to `task` difficulty.
 - High variance indicates that some tasks are inherently harder for the model,
 regardless of perturbation.

**Relevance**:
- **SC-007**: Requires quantifying the variance component of the 'task' random effect.
- **US-3**: Implemented in `code/analysis/statistics.py` to provide a more robust
 analysis than simple paired tests, accounting for task-specific variability.

---

## 6. Sensitivity Analysis

**Definition**: An evaluation of how the study's conclusions change when key
parameters (specifically, the semantic similarity threshold) are varied.

**Parameters Tested**:
- Thresholds: `{0.85, 0.90, 0.95, 0.99}`

**Metric**:
- **Delta from Baseline**: The difference in Pass@1 degradation between the
 tested threshold and the primary baseline (0.95).

**Purpose**:
- To demonstrate that the observed robustness effects are not an artifact of a
 specific threshold choice.
- If results are consistent across the range, the findings are considered robust.

**Relevance**:
- **FR-009**: Explicitly requires analysis across these specific thresholds.
- **US-3**: Generates `data/processed/sensitivity_report.csv` to visualize stability.

---

## 7. Error Classification

**Definition**: A stratified sampling and tagging process to categorize execution
failures into specific error types.

**Categories**:
- **Syntax Error**: Code fails to parse or compile.
- **Logic Error**: Code runs but produces incorrect output or fails unit tests.
- **Timeout**: Execution exceeds the time limit (10s per test case).
- **OOM**: Out of Memory (if applicable).

**Methodology**:
- Stratified by perturbation type.
- Sample size: Up to 50 failures or 100% if fewer than 50 exist.
- Random seed: 42 for reproducibility.

**Relevance**:
- **US-3**: Helps diagnose *why* perturbations cause failures (e.g., typos causing
 syntax errors vs. synonyms causing logic errors).

---

## References

- **Spec**: `specs/001-evaluating-robustness-llm-code/spec.md` (FR-001 to FR-013)
- **Plan**: `specs/001-evaluating-robustness-llm-code/plan.md`
- **Implementation**: `code/analysis/statistics.py`, `code/analysis/report_generator.py`