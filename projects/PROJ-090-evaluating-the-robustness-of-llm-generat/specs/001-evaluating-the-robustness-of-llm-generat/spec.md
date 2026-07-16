# Feature Specification: Evaluating the Robustness of LLM-Generated Code to Input Perturbations

**Feature Branch**: `001-evaluating-robustness-llm-code`  
**Created**: 2026-07-03  
**Status**: Draft  
**Input**: User description: "Evaluating the Robustness of LLM-Generated Code to Input Perturbations"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Acquisition and Semantic-Preserving Perturbation Generation (Priority: P1)

The system MUST download the HumanEval dataset and programmatically generate up to 3 perturbed prompt variants per task using three distinct rule-based transformations: (1) synonym substitution in non-keyword tokens, (2) random character typo injection in function descriptions, and (3) syntactic rephrasing of the problem statement. The system MUST validate semantic equivalence using a non-LLM transformer model (sentence-transformers/all-MiniLM-L6-v2) to calculate cosine similarity; only perturbations with a semantic similarity score > 0.95 are retained for the primary analysis. The system MUST retain the raw similarity scores for all generated candidates to enable post-hoc sensitivity analysis. Invalid or semantically divergent perturbations MUST be logged and excluded from the primary set but retained in the raw log.

**Why this priority**: This is the foundational step defining the independent variables. Without a verified set of semantically-equivalent but surface-different prompts, the study cannot distinguish between model fragility and prompt misinterpretation. The high threshold (0.95) defines the "high-fidelity" scope, acknowledging that more aggressive noise may yield different results (addressed in FR-013).

**Independent Test**: The pipeline can be tested by running the perturbation generator on a mock HumanEval task and verifying the output JSON contains up to 3 distinct variants (or fewer if semantic validation fails), correctly tagged by type (`synonym`, `typo`, `rephrase`), with a recorded raw semantic similarity score for every candidate and a filtered score > 0.95 for retained items, without running model inference.

**Acceptance Scenarios**:

1. **Given** the HumanEval dataset is accessible via HuggingFace Datasets, **When** the ingestion script runs, **Then** All programming tasks are downloaded locally..
2. **Given** a base prompt, **When** the perturbation module runs, **Then** up to 3 candidate variants are generated, and those with a semantic similarity score ≤ 0.95 are excluded from the final primary dataset but kept in the raw log.

---

### User Story 2 - CPU-Compatible Model Inference and Execution (Priority: P2)

The system MUST execute a quantized (low-bit) StarCoder2-3B model on CPU hardware using `bitsandbytes` quantization without CUDA dependencies and run the generated code in a sandboxed environment to capture pass/fail results. The system MUST enforce a strict timeout of 30 seconds per generation and A fixed duration per test case execution.

**Why this priority**: This is the core experimental engine. It must respect the compute constraints (limited RAM, time limits) while producing the raw data (code correctness) needed for analysis.

**Independent Test**: The pipeline can be tested by running inference on a single sample task and verifying the output code executes in the sandbox, returning a pass/fail status within the defined timeout, independent of statistical analysis.

**Acceptance Scenarios**:

1. **Given** a perturbed prompt, **When** the model inference runs, **Then** the code is generated without CUDA errors, within the A memory limit is imposed to constrain resource usage during the research phase., and completes within 30 seconds.
2. **Given** generated code, **When** the sandbox executor runs, **Then** the test suite is executed with a 10-second timeout per test case, returning a pass/fail status or a timeout error.

---

### User Story 3 - Statistical Analysis, Multiplicity Correction, and Error Classification (Priority: P3)

The system MUST calculate pass@1 rates for original vs. perturbed prompts, apply McNemar's test for paired comparison per perturbation type, apply Bonferroni correction for multiple comparisons, and classify errors to determine the impact of perturbations. The system MUST perform a sensitivity analysis on the semantic similarity threshold by re-scoring the raw candidate pool with thresholds ∈ {high-confidence values} and reporting the variation in headline pass rates to quantify survivorship bias. The system MUST also perform a Mixed-Effects Logistic Regression with 'task' as a random effect to account for clustering.

**Why this priority**: This delivers the scientific value of the project. It transforms raw execution logs into interpretable research findings, ensuring methodological soundness regarding inference framing, multiplicity, clustering, and threshold justification.

**Independent Test**: The pipeline can be tested by feeding a mock CSV of pass/fail results and threshold metadata into the analysis script and verifying the statistical output (p-values, corrected alpha, mixed-effects coefficients, sensitivity report) matches expected calculations.

**Acceptance Scenarios**:

1. **Given** paired success/failure counts for original vs. perturbed prompts, **When** McNemar's test runs, **Then** a p-value is returned, and if >1 hypothesis is tested, a Bonferroni-corrected p-value is also returned.
2. **Given** a set of semantic thresholds {0.85, 0.90, 0.95, 0.99}, **When** the sensitivity analysis runs, **Then** the system reports the pass@1 rate for each threshold and the absolute difference in rates between the primary (0.95) and adjacent thresholds.
3. **Given** a failed execution, **When** the error classifier runs, **Then** the failure is tagged as syntax, logic, or hallucination for a a stratified random sample of failures (or all if total failures ≤ 50).
4. **Given** the full dataset of results, **When** the Mixed-Effects model runs, **Then** the system outputs the fixed effect of perturbation type and the variance component for the 'task' random effect.

---

### Edge Cases

- What happens when the sandbox execution times out? (System MUST record this as a failure and tag it as "timeout" in the error log).
- How does the system handle model inference OOM errors? (System MUST log the error, skip the sample to continue the batch, and flag the sample as "OOM" in the results).
- What happens if the semantic similarity scorer fails to return a score? (System MUST exclude the perturbation and log the failure reason).
- What happens if the total number of valid perturbations falls below the target due to strict semantic filtering? (System MUST proceed with available data but flag the reduced sample size in the final report).
- What happens if the total number of valid perturbations exceeds the budget cap? (System MUST prioritize original prompts, then fill remaining slots with perturbed prompts in a deterministic order until the cap is reached).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download the HumanEval dataset from HuggingFace Datasets (`openai_humaneval`). (See US-1)
- **FR-002**: System MUST attempt to generate up to 3 perturbation variants per task using synonym substitution, typo injection, and syntactic rephrasing, retaining only those with a semantic similarity score > 0.95 for the primary dataset. (See US-1)
- **FR-003**: System MUST validate semantic equivalence using the `sentence-transformers/all-MiniLM-L6-v2` model with cosine similarity, retaining only perturbations with a score > 0.95, while storing raw scores for all candidates. (See US-1)
- **FR-004**: System MUST perform model inference using a `bitsandbytes` 4-bit quantized StarCoder2-3B configuration on CPU with offload, ensuring memory usage stays ≤ 7 GB. (See US-2)
- **FR-005**: System MUST enforce a reasonable timeout for model generation and a 10-second timeout for test case execution. (See US-2)
- **FR-006**: System MUST calculate pass@1 rates separately for the original prompts and each valid perturbation type. (See US-3)
- **FR-007**: System MUST apply McNemar's test separately for each perturbation type (Original vs. Synonym; Original vs. Typo; Original vs. Rephrase) by aggregating contingency tables across all tasks for each comparison. (See US-3)
- **FR-008**: System MUST apply Bonferroni correction for multiple comparisons when testing >1 hypothesis across perturbation types. (See US-3)
- **FR-009**: System MUST perform a sensitivity analysis on the semantic similarity threshold by re-scoring the full candidate pool with thresholds ∈ {0.85, 0.90, 0.95, 0.99} and reporting the variation in pass@1 rates. (See US-3)
- **FR-010**: System MUST classify failures into syntax, logic, or hallucination types for all failures if the total count is ≤ 50, otherwise for a stratified random sample of 50 failures. (See US-3)
- **FR-011**: System MUST limit total generations to a sufficient number of samples by prioritizing all original tasks and filling the remaining budget with perturbed prompts in a deterministic order until the cap is reached. (See US-2)
- **FR-012**: System MUST perform a Mixed-Effects Logistic Regression with 'task' as a random effect to account for clustering of perturbations within tasks. (See US-3)
- **FR-013**: System MUST report the variation in pass@1 rates across the threshold sweep {0.85, 0.90, 0.95, 0.99} to quantify the impact of the high-fidelity filter (survivorship bias). (See US-3)

### Key Entities

- **Task**: A programming problem from HumanEval containing a function signature, docstring, and test cases.
- **Prompt**: The text input sent to the model, existing in original or perturbed states.
- **Generation**: The code output produced by the model for a specific prompt.
- **Result**: The execution outcome (pass/fail/error/timeout) of the generated code against test cases.
- **Similarity Score**: A float value (0.0–1.0) representing the semantic equivalence between original and perturbed prompts, calculated via cosine similarity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Pass@1 degradation is measured against the original prompt baseline. A robustness failure is confirmed if McNemar's test yields a Bonferroni-corrected p ≤ 0.05 AND the absolute pass@1 drop is ≥ 5% relative to the baseline. (See US-3)
- **SC-002**: Statistical significance is measured against the Bonferroni-corrected alpha level (α = 0.05 / 3 comparisons) to validate associational claims. (See US-3)
- **SC-003**: Total job runtime is measured against the -hour GitHub Actions free-tier limit. (See US-2)
- **SC-004**: Memory usage is measured against the available RAM constraint during inference. (See US-2)
- **SC-005**: Sensitivity of results is measured against the variation in pass@1 rates across the threshold sweep {0.85, 0.90, 0.95, 0.99}. (See US-3)
- **SC-006**: Sample count is measured against a predefined feasibility limit to ensure feasibility. (See US-2)
- **SC-007**: Clustering effects are measured against the variance component of the 'task' random effect in the Mixed-Effects model. (See US-3)

## Assumptions

- The HumanEval dataset is accessible via HuggingFace Datasets without authentication barriers in the CI environment.
- The GitHub Actions runner provides Docker or subprocess sandboxing capabilities for code execution.
- A StarCoder2 3B model variant is available in a format compatible with CPU inference using `transformers` and `bitsandbytes` 4-bit quantization without requiring CUDA-specific libraries.
- The `sentence-transformers/all-MiniLM-L-v2` model is small enough to run on CPU within the 6-hour window and does not significantly impact the total runtime budget.
- A sufficient sample size will be established to achieve statistical power for McNemar's test and Mixed-Effects regression given the expected effect size for semantically-equivalent perturbations.
- Network bandwidth in the CI environment is sufficient to download the model weights (several gigabytes) and the HumanEval dataset within the 6-hour window.
- The perturbations generated by rule-based transformations (synonym, typo, rephrase) are deterministic and do not alter the semantic intent of the original task beyond the intended noise, provided the similarity score > 0.95.
- The study results are explicitly scoped to "high-fidelity" perturbations (similarity > 0.95); results may differ for lower similarity thresholds as quantified by the sensitivity analysis.