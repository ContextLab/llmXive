# Feature Specification: Evaluating the Impact of Code Style on LLM Code Understanding and Generation

**Feature Branch**: `001-evaluating-code-style-impact`  
**Created**: 2024-05-21  
**Status**: Draft  
**Input**: User description: "Evaluating the Impact of Code Style on LLM Code Understanding and Generation"

## User Scenarios & Testing

### User Story 1 - Style-Aware Code Transformation (Priority: P1)

As a researcher, I want to systematically transform a base corpus of Python functions into multiple style variants (formatting, naming, commenting) so that I can isolate the specific impact of each stylistic dimension on LLM performance.

**Why this priority**: This is the foundational data preparation step. Without a controlled, orthogonal set of style variants, no subsequent analysis of performance differences is possible. It directly enables the core experimental design.

**Independent Test**: Can be fully tested by running the transformation pipeline on a small sample (e.g., 10 functions) and verifying that exactly 8 distinct variants are generated per function, with correct application of Black formatting, identifier renaming, and comment stripping/retention.

**Acceptance Scenarios**:

1. **Given** a valid Python function from the CodeSearchNet dataset, **When** the transformation pipeline is executed with all three factors (formatting, naming, commenting) enabled, **Then** the output directory contains exactly 8 files representing the full factorial design (2 levels × 2 levels × 2 levels).
2. **Given** a function with original comments, **When** the "strip comments" factor is applied, **Then** all comment lines (starting with `#`) and docstrings are removed from the output variant while preserving the code logic.
3. **Given** a function with descriptive identifiers, **When** the "generic naming" factor is applied, **Then** all identifiers are replaced with short generic tokens (e.g., `var1`, `func2`) according to a deterministic mapping, ensuring no syntax errors are introduced.

---

### User Story 2 - LLM Task Execution & Metric Collection (Priority: P2)

As a researcher, I want to execute three specific LLM tasks (completion, bug detection, summarization) on each style variant and automatically collect performance metrics (Exact Match, CodeBLEU, Precision/Recall/F1, ROUGE-L) so that I can quantify the performance impact of style variations.

**Why this priority**: This implements the core evaluation logic. It transforms the prepared data into measurable outcomes, directly addressing the research question regarding LLM sensitivity to style.

**Independent Test**: Can be fully tested by running the evaluation script on a pre-defined subset of 5 functions with known expected outputs, verifying that metrics are calculated correctly and saved in a structured CSV format.

**Acceptance Scenarios**:

1. **Given** a set of style variants for a function, **When** the code completion task is run, **Then** the system generates the missing last line for each variant and calculates the Exact Match and CodeBLEU scores against the ground truth completion provided in the dataset schema.
2. **Given** a style variant with an injected bug (generated via diverse mutation operators), **When** the bug detection task is run, **Then** the system correctly classifies the input as "buggy" or "clean" based on the mutation intent and records Precision, Recall, and F1 scores.
3. **Given** a style variant (including "stripped" input variants), **When** the summarization task is run, **Then** the system generates a one-sentence description and computes ROUGE-L and BLEU scores against the *original* ground truth docstring (which is preserved and not stripped), **and logs the specific mutation type** for any injected bug samples to enable analysis of pattern learning (See US-2, FR-008).

---

### User Story 3 - Statistical Analysis & Reporting (Priority: P3)

As a researcher, I want to perform a robust statistical analysis on the collected metrics to determine the statistical significance of style factors and their interactions, and generate a report with effect sizes and corrected p-values, so that I can draw valid conclusions about style impact.

**Why this priority**: This provides the scientific rigor required to answer the research question. It moves beyond raw metrics to inferential statistics, addressing the "impact" aspect of the title.

**Independent Test**: Can be fully tested by running the analysis script on a synthetic dataset with known effect sizes, verifying that the analysis correctly identifies significant factors, applies appropriate transformations or non-parametric tests if normality is violated, and reports the method used.

**Acceptance Scenarios**:

1. **Given** a dataset of metrics, **When** the statistical analysis is run, **Then** the system performs a normality check (Shapiro-Wilk) and selects an appropriate mixed-effects model (linear or generalized) based on the data distribution.
2. **Given** significant main effects, **When** post-hoc pairwise comparisons are performed, **Then** the results include Bonferroni-corrected p-values to control for family-wise error rate.
3. **Given** the analysis results, **When** the report is generated, **Then** it includes visualizations (e.g., interaction plots) and a summary table with columns for Factor, Estimate, Standard Error, t-value, and p-value, saved to the `results/` directory.

### User Story 4 - Semantic Opacity Control (Priority: P3)

As a researcher, I want to explicitly measure the impact of the "generic naming + stripped comments" condition (semantic opacity) as a distinct confounding variable, so that I can distinguish between style impact and semantic loss in the summarization task.

**Why this priority**: The "generic naming" factor combined with "stripped comments" creates a "black box" input that may render the summarization task unsolvable. This must be measured as a specific confound rather than assumed to be a style effect.

**Independent Test**: Can be fully tested by running the summarization task specifically on the "generic naming + stripped comments" variant and comparing the performance drop against the "clean naming + stripped comments" variant.

**Acceptance Scenarios**:

1. **Given** a function with "generic naming" and "stripped comments" applied, **When** the summarization task is run, **Then** the system records the performance metrics and explicitly flags the sample as part of the "Semantic Opacity" control group.
2. **Given** the collected metrics, **When** the analysis is run, **Then** the report includes a specific comparison of performance between the "Semantic Opacity" group and the baseline "clean naming + stripped comments" group to quantify the confound.

---

### Edge Cases

- What happens when a code transformation (e.g., identifier renaming) inadvertently breaks Python syntax? (System must validate syntax of all variants before LLM submission).
- How does the system handle functions where the original docstring is missing or empty for the summarization task? (System must skip or flag these samples rather than crashing).
- How does the system handle timeout or resource exhaustion during LLM inference on the CI runner? (System must implement a retry mechanism with a maximum of 3 attempts and log failures).

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate 8 distinct style variants per base function by orthogonally combining 2 levels of formatting (Black vs. Minified), 2 levels of naming (Meaningful vs. Generic), and 2 levels of commenting (Present vs. Stripped). The "Stripped" variant removes comments from the *input* to the LLM but preserves the original docstring in the dataset as the ground truth for evaluation (See US-1).
- **FR-002**: System MUST validate the syntactic correctness of all generated style variants using a Python parser before submitting them to the LLM (See US-1).
- **FR-003**: System MUST execute a selected code-generation LLM to perform code completion, bug detection, and summarization tasks on each variant (See US-2).
- **FR-004a**: For the code completion task, System MUST calculate Exact Match and CodeBLEU scores by comparing the LLM output against the ground truth completion provided in the dataset (See US-2).
- **FR-004b**: For the bug detection task, System MUST calculate Precision, Recall, and F1 scores by comparing the LLM classification against the ground truth label where 'buggy' is true only if a mutation was applied (per FR-008) and the sample is part of the injected half, otherwise 'clean' (See US-2, FR-008).
- **FR-004c**: For the summarization task, System MUST calculate ROUGE-L and BLEU scores (algorithmic metrics) by comparing the LLM output against the original ground truth docstring from the **docstring field of the CodeSearchNet dataset** (See US-2, US-4).
- **FR-005**: Upon successful completion of the Verified Accuracy enforcement step (FR-010), the system MUST perform a mixed-effects modeling analysis (linear or generalized) with fixed effects for the three style factors and random intercepts for the original function ID. The system MUST first perform a normality check (Shapiro-Wilk) and apply a robust alternative (e.g., non-parametric permutation test) if residuals are non-normal. The output MUST include a structured table with columns for Factor, Estimate, Standard Error, t-value, and p-value (See US-3).
- **FR-006**: System MUST log the specific mutation type for every injected bug sample to enable analysis of whether the model learns patterns or semantics (See US-2, FR-008).
- **FR-007**: System MUST perform a Tokenization Impact Analysis by counting tokens for each style variant and reporting the correlation between token count changes and performance drops. If token count changes exceed a threshold T (to be determined in implementation) and correlate with performance drops, the system MUST flag the result as potentially confounded (See US-2, US-3).
- **FR-008**: For the bug detection task, the system MUST generate a balanced dataset where [deferred] of samples are clean variants and [deferred] are injected bug variants, ensuring the classification task measures style sensitivity against a controlled baseline rather than anomaly detection (See US-2).
- **FR-010**: System MUST execute a pre-flight validation script that enforces Constitution Principle II (Verified Accuracy) by verifying all citations and data sources before any LLM inference or statistical analysis occurs (See US-3).

### Key Entities

- **StyleVariant**: A specific version of a base function with applied formatting, naming, and commenting transformations.
- **TaskResult**: The output of a LLM task execution, including the generated text, the calculated performance metrics, and the specific task type.
- **GroundTruthLabel**: The reference output provided in the dataset schema (e.g., completion string, bug label, original docstring) used for metric calculation.
- **StatisticalModel**: The mixed-effects model (linear or generalized) used to analyze the relationship between style factors and performance metrics.
- **MutationType**: A categorical label describing the specific mutation operator applied to generate a bug (e.g., "variable_swap", "operator_flip").

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The proportion of successfully generated and syntactically valid style variants is measured and recorded; the target proportion is deferred to the implementation phase (See US-1).
- **SC-002**: The performance metrics (Exact Match, CodeBLEU, Precision, Recall, F1, ROUGE-L, BLEU) are measured against the **docstring field of the CodeSearchNet dataset** to determine accuracy (See US-2, FR-004c).
- **SC-003**: The statistical significance of style factors is measured against the null hypothesis (no effect) using a p-value threshold of 0.05, with Bonferroni correction for multiple comparisons (See US-3).
- **SC-004**: The effect sizes (η² or equivalent) for each style factor are measured to quantify the magnitude of the impact on LLM performance (See US-3).
- **SC-005**: The total compute time for the entire pipeline (data transformation, inference, analysis) is measured against the CI runner limit. (See US-1, US-2, US-3).
- **SC-006**: The correlation between token count changes and performance drops is measured to assess potential confounding (See FR-007, US-2).

## Assumptions

- The CodeSearchNet Python subset contains sufficient functions with docstrings to support the target scale after filtering for compilability.
- The selected code-generation LLM (e.g., CodeGen) can be loaded and executed within the limited RAM of the GitHub Actions free-tier runner without requiring GPU acceleration.
- The `black` formatter and custom renaming scripts will not introduce semantic changes that alter the logical behavior of the code, only surface-level style.
- The injected bugs for the bug detection task are generated using a diverse set of mutation operators (e.g., variable swap, operator flip) to prevent trivial pattern matching.
- The mixed-effects modeling approach (linear or generalized) is appropriate for the data structure and does not require complex hierarchical modeling beyond random intercepts for function ID.
- The Bonferroni correction is sufficient to control for family-wise error rate given the number of pairwise comparisons performed.
- The HuggingFace `datasets` library and `transformers` pipeline are compatible with the CPU-only environment and do not require CUDA-specific dependencies.
- The CodeGen-2B model (or equivalent selected model) is available via the HuggingFace Hub and can be accessed without authentication restrictions that would block CI execution.
- The ground truth docstrings for the summarization task are preserved in the dataset and are not affected by the "strip comments" transformation applied to the input variants.
- The pipeline architecture is designed to include a pre-flight validation step that enforces Constitution Principle II (Verified Accuracy) before any LLM inference or statistical analysis occurs.
- The Verified Accuracy enforcement step (FR-010) is a mandatory prerequisite for the statistical analysis workflow described in FR-005.