# Feature Specification: ShutterMuse: Capture-Time Photography Guidance with MLLMs

**Feature Branch**: `001-shutter-muse-guide`  
**Created**: 2026-06-30  
**Status**: Draft  
**Input**: User description: "ShutterMuse: Capture-Time Photography Guidance with MLLMs"

## User Scenarios & Testing

### User Story 1 - Systematic Error Categorization (Priority: P1)

The system must ingest a set of images from the AVA and COCO datasets, generate capture-time guidance using selected MLLMs, and automatically categorize the resulting errors (e.g., "Hallucinated Object," "Incorrect Rule Application") by comparing them against ground-truth annotations.

**Why this priority**: This is the foundational capability. Without a reliable mechanism to categorize errors against ground truth, no analysis of biases or architectural limitations is possible. It delivers the primary value of the research: a structured dataset of failure modes.

**Independent Test**: Can be fully tested by running the error-categorization script on a small, fixed subset of 50 images and verifying that the output CSV contains correctly labeled error types matching manual inspection of the model outputs.

**Acceptance Scenarios**:

1. **Given** an image from the AVA dataset with known ground-truth composition tags, **When** the system runs the MLLM inference and compares the output to the tags, **Then** the system MUST log a specific error category (e.g., "Rule of Thirds Violation") if a discrepancy is detected.
2. **Given** an image where the model hallucinates an object not present in the ground truth, **When** the system parses the model's text output, **Then** the system MUST tag the output as "Hallucinated Object."
3. **Given** a model output that correctly identifies a composition principle, **When** the system validates against ground truth, **Then** the system MUST record the result as "Correct" and exclude it from the error count.

---

### User Story 2 - Bias Correlation Analysis (Priority: P2)

The system must correlate the frequency of specific error types with demographic and environmental metadata (e.g., subject gender, lighting conditions) derived from an external, validated annotation pipeline (e.g., FairFace) to identify data-driven biases.

**Why this priority**: This addresses the core research question regarding whether errors stem from training data distribution gaps. It builds upon the categorized errors from US-1 to reveal systematic patterns.

**Independent Test**: Can be fully tested by executing the correlation analysis script on the categorized error data (with demographics inferred via the external pipeline) and verifying that the output includes statistical significance tests (e.g., Chi-square or Fisher's Exact) linking error rates to specific metadata groups.

**Acceptance Scenarios**:

1. **Given** a dataset of categorized errors and associated image metadata (inferred via FairFace with confidence ≥ 0.85), **When** the system runs the correlation analysis, **Then** it MUST output a Chi-square statistic and p-value (or Fisher's Exact p-value if cell counts < 5) for the relationship between "Subject Demographic" and "Error Type."
2. **Given** a specific error type (e.g., "Pose Suggestion Bias"), **When** the system aggregates data by lighting condition, **Then** it MUST report the error rate per lighting category to identify if low-light conditions exacerbate the bias.
3. **Given** no significant correlation found in the data, **When** the system completes the analysis, **Then** it MUST explicitly report a non-significant result rather than forcing a correlation.

---

### User Story 3 - Architectural Comparison (Priority: P3)

The system must compare error patterns across at least three distinct MLLM architectures (e.g., LLaVA-1.6, Qwen-VL, GPT-4V) using counterfactual prompting to isolate reasoning-based failures versus data-driven ones.

**Why this priority**: This differentiates between errors caused by the model's reasoning capabilities and those caused by shared training data. It is critical for the "Methodology" section of the research but relies on the successful execution of US-1 and US-2.

**Independent Test**: Can be fully tested by running the comparison script on the aggregated error data from the three models (including counterfactual test results) and verifying that the output includes a comparative table of error rates per model architecture and per error cause (reasoning vs. data).

**Acceptance Scenarios**:

1. **Given** error logs from three different MLLMs processed on the same image subset (including counterfactual prompts), **When** the system compares the error distributions, **Then** it MUST identify which architecture has the lowest rate of "Reasoning-Based Errors" (e.g., logical inconsistencies in advice under counterfactual conditions).
2. **Given** a specific composition principle (e.g., "Leading Lines"), **When** the system compares models, **Then** it MUST report if one model consistently outperforms others on this specific principle, indicating an architectural advantage.
3. **Given** conflicting results between models, **When** the system aggregates the findings, **Then** it MUST flag the specific principle where model performance diverges most significantly for further review.

---

### Edge Cases

- **What happens when ground-truth metadata is missing?** The system MUST skip the image for bias analysis but include it for general error categorization if composition tags exist.
- **How does the system handle API rate limits for GPT-4V?** The system MUST implement a retry mechanism with exponential backoff (max 3 retries) and pause execution if the limit is exceeded for > 5 minutes.
- **What happens if an MLLM output is non-textual or garbled?** The system MUST log the raw output as "Parsing Failure" and exclude it from the statistical analysis to prevent skewing results.
- **What happens if demographic inference confidence is < 0.85?** The system MUST exclude the image from demographic bias analysis (but retain for general error logging) to ensure ground-truth quality.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and parse the AVA and COCO datasets to extract images and ground-truth composition/pose annotations. (See US-1)
- **FR-002**: The system MUST execute standardized prompts on at least three distinct MLLMs (LLaVA-1.6, Qwen-VL, GPT-4V) to generate capture-time guidance. (See US-1)
- **FR-003**: The system MUST parse model outputs and categorize discrepancies into predefined error types (e.g., "Hallucinated Object," "Incorrect Rule Application") by comparing against ground truth. (See US-1)
- **FR-004**: The system MUST perform statistical tests for independence between error types and demographic groups: calculate expected cell frequencies; if any expected frequency < 5, use Fisher's Exact Test; otherwise, use Chi-square test. (See US-2, US-3)
- **FR-005**: The system MUST generate a comparative report summarizing error rates per model architecture and per demographic group. (See US-3)
- **FR-006**: The system MUST implement a retry mechanism with exponential backoff (max 3 retries) for API calls to external models. (See Edge Cases)
- **FR-007**: The system MUST handle missing metadata by excluding the specific record from bias analysis while retaining it for general error logging. (See Edge Cases)
- **FR-008**: The system MUST infer subject demographics using a validated external tool (e.g., FairFace) and include only samples where the inference confidence score is ≥ 0.85 in the demographic bias analysis. (See US-2)
- **FR-009**: The system MUST employ counterfactual prompting (e.g., "What if the lighting was X?") to isolate reasoning-based failures (logical inconsistencies) from data-driven failures (factual hallucinations) across model architectures. (See US-3)

### Key Entities

- **Image Sample**: A unit of analysis containing the image file, ground-truth composition tags, and associated demographic/lighting metadata (inferred via FR-008 or native tags).
- **Model Output**: The text response generated by an MLLM in response to a capture-time guidance prompt.
- **Error Record**: A structured entry linking an Image Sample, Model Output, and a specific Error Category.
- **Analysis Result**: A statistical aggregate (e.g., Chi-square value, p-value, error rate) derived from a set of Error Records.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The rate of successfully categorized errors is measured against the total number of valid model outputs (excluding parsing failures). (See FR-003)
- **SC-002**: The statistical significance of bias correlations (p-value) is measured against the standard alpha threshold of 0.05. (See FR-004)
- **SC-003**: The variation in error rates across different MLLM architectures is measured against a fixed human-expert baseline error rate of [deferred] (median from Smith et al. 2022, n=500). (See FR-005)
- **SC-004**: The completeness of metadata coverage (percentage of images with demographic tags) is measured against the total dataset size. (See FR-008)
- **SC-005**: The reproducibility of the error categorization is measured by re-running the script on a fixed subset and verifying Cohen's kappa coefficient ≥ 0.80 in error labels. (See US-1)

## Assumptions

- The AVA and COCO datasets provide sufficient ground-truth metadata (composition tags, lighting) for general error categorization, but demographic metadata MUST be derived via an external inference pipeline (FR-008) as these datasets do not natively contain subject demographics.
- The selected MLLMs (LLaVA-1.6, Qwen-VL, GPT-4V) are accessible via the specified interfaces (local API for open models, cloud API for GPT-4V) and their output formats are parseable by the system.
- The free-tier GitHub Actions runner (2 CPU, 7 GB RAM) is sufficient for running the inference and analysis on a sampled subset of the datasets (e.g., 500-1000 images) without GPU acceleration.
- The "capture-time" guidance simulation via static prompts is a valid proxy for real-time interactive guidance for the purpose of identifying systematic error patterns.
- The demographic inference tool (e.g., FairFace) provides sufficient accuracy for bias analysis when filtered by a confidence threshold of ≥ 0.85.
- The statistical test selection logic (FR-004) correctly handles the sparsity of the final filtered dataset (post-confidence threshold) to ensure valid p-values.
- The human-expert baseline error rate of [deferred] (Smith et al. 2022) is a valid and measurable reference for evaluating architectural performance.