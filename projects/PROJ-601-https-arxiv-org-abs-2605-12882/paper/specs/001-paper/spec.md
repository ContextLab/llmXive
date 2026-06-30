# Feature Specification: CiteVQA Reproduction & Validation Paper

**Feature Branch**: `601-paper-citevqa-validation`
**Created**: 2026-06-30
**Status**: Draft
**Input**: Research-stage artifacts (spec.md, plan.md, tasks.md), code_summary, data_summary, and reviewer feedback on implementation correctness and filesystem hygiene.

## User Scenarios & Testing

### User Story 1 - Reproducibility & Execution Transparency (Priority: P1)

A peer reviewer or independent researcher MUST be able to replicate the exact experimental setup described in the paper by following the "Reproducibility" section, running the provided scripts on a standard CPU environment, and obtaining the primary results (SAA score) without requiring proprietary hardware or hidden data.

**Why this priority**: The core value of a reproduction paper is trust. If a reader cannot execute the pipeline to verify the "Strict Attributed Accuracy" metric, the paper's claims regarding WYSIATI bias mitigation lose validity. This is the foundational requirement for scientific integrity.

**Independent Test**: A reviewer executes the `infer/run.py` and `eval/run.py` scripts using the documented sample configuration. The test passes if the system generates `outputs/evaluation_report.json` with the expected schema and the SAA score matches the reported value within a 0.01 tolerance (accounting for non-determinism in sampling).

**Acceptance Scenarios**:

1. **Given** the repository is cloned and the `external/CiteVQA` submodule is initialized, **When** the reviewer runs the provided `reproduce.sh` script on a CPU-only machine, **Then** the pipeline completes successfully, generating `outputs/infer_results.jsonl` and `outputs/evaluation_report.json` without manual intervention.
2. **Given** the paper claims CPU-only feasibility, **When** the reviewer inspects the execution logs, **Then** they confirm no CUDA/GPU calls were made and memory usage remained within the documented <7 GB limit.

---

### User Story 2 - Attribution Hallucination Diagnosis (Priority: P2)

A domain expert or student MUST be able to inspect the `outputs/evaluation_report.json` and the detailed `outputs/validation_log.json` to distinguish between "Answer Correct/Region Wrong" (Attribution Hallucination) and "Answer Wrong" cases, thereby verifying the paper's claim that the SAA metric effectively penalizes the WYSIATI bias.

**Why this priority**: This story addresses the specific scientific contribution of the paper: the analysis of *why* models fail (coherence vs. truth). Without granular breakdowns of error types, the paper cannot substantiate its argument about the limitations of standard accuracy metrics.

**Independent Test**: A script parses the generated `evaluation_report.json`. The test passes if the `attribution_hallucination_rate` is explicitly calculated and the breakdown of `answer_only_correct` vs. `region_only_correct` counts is present and sums to the total error count.

**Acceptance Scenarios**:

1. **Given** the evaluation report contains a set of predictions, **When** the reader examines the error breakdown, **Then** they can identify a specific count of cases where the answer was correct but the bounding box was incorrect (Attribution Hallucination).
2. **Given** the validation log, **When** a reader filters for "skipped" records, **Then** they can see the specific reasons (e.g., "missing_bbox", "missing_image") ensuring the dataset integrity checks described in the paper were actually performed.

---

### User Story 3 - Data & Methodological Transparency (Priority: P3)

A future researcher extending this work MUST be able to locate the exact data subsets used, the specific model configuration (quantization, batch size), and the IoU threshold parameters used for the SAA calculation to ensure the results are not artifacts of a specific, undocumented setup.

**Why this priority**: While the execution (P1) and error analysis (P2) are immediate, the long-term utility of the paper depends on the ability to extend or critique the methodology. Ambiguity here prevents future research.

**Independent Test**: A reader reviews the `docs/reproducibility/pipeline_validation.md` and `outputs/evaluation_report.json`. The test passes if the IoU threshold, model quantization level, and sample size are explicitly stated and match the code implementation.

**Acceptance Scenarios**:

1. **Given** the paper claims a specific IoU threshold (e.g., 0.5), **When** the reader checks the `eval/metrics.py` source code referenced in the documentation, **Then** the threshold is hard-coded or clearly configurable in the arguments.
2. **Given** the paper discusses memory constraints, **When** the reader checks the `data/validate_dataset.py` logic, **Then** they can verify the streaming/batching mechanism that ensures the <7 GB RAM constraint.

---

## Edge Cases

- **What happens if the ground-truth bounding boxes are ambiguous or missing in the dataset?** The system (and paper) MUST explicitly state that such records are excluded from the SAA calculation and logged in `outputs/validation_log.json` to prevent skewing the metric. The paper must report the `skipped_count` as a metric of data quality.
- **What if the CPU inference produces non-deterministic results due to floating-point variations?** The paper MUST acknowledge this limitation and define the acceptable variance range for the SAA score, or mandate a fixed random seed in the reproduction script to ensure exact reproducibility.
- **How does the system handle a scenario where the model generates a bounding box outside the [0,1] normalized range?** The evaluation logic MUST clamp or reject such predictions and log them as "Format Error" rather than calculating a negative IoU, ensuring the SAA score remains mathematically valid.

## Required Sections

The paper artifact must contain the following sections, mapped to the research implementation:

1. **Abstract**: Summarize the reproduction of CiteVQA, the CPU-only constraint, and the key finding regarding Attribution Hallucination rates.
2. **Introduction**: Contextualize the WYSIATI bias in MLLMs and the necessity of spatial attribution metrics (SAA).
3. **Methods**: Detail the experimental setup (CPU environment, model quantization), the dataset validation process (`data/validate_dataset.py`), and the SAA calculation logic (IoU thresholding, error categorization).
4. **Results**: Present the SAA score, the `attribution_hallucination_rate`, and the breakdown of error types derived from `outputs/evaluation_report.json`. Include the `skipped_count` from `outputs/validation_log.json`.
5. **Discussion**: Analyze the implications of the high attribution hallucination rate for the "coherence vs. truth" debate. Discuss the feasibility of CPU-only MLLM benchmarking.
6. **References**: Cite the original CiteVQA paper, the transformers library, and relevant literature on WYSIATI bias.
7. **Reproducibility Appendix**: Provide the exact commands, environment variables, and a link to the `docs/reproducibility/pipeline_validation.md` for full pipeline replication. **MUST explicitly list the random seed configuration and the exact `transformers`/`torch` versions used.**

## Required Figures

1. **Figure 1: The SAA Calculation Workflow**: A flowchart illustrating the pipeline from `infer/run.py` (prediction) to `eval/run.py` (IoU calculation and error categorization), highlighting the branching logic for "Answer Correct/Region Wrong" vs. "Answer Wrong".
 * *Source*: Logic in `eval/saa_scoring.py` and `eval/metrics.py`.
 * *Mandatory Requirement*: This figure MUST include a self-contained legend defining **'SAA'**, **'IoU'**, and **'Attribution Hallucination'** without requiring the reader to consult the Methods section.

2. **Figure 2: Error Distribution Bar Chart**: A bar chart showing the counts of `both_correct`, `answer_only_correct`, `region_only_correct` (Attribution Hallucination), and `both_wrong` cases.
 * *Source*: Aggregated data from `outputs/evaluation_report.json`. **The research implementation MUST generate these specific breakdowns (answer_only_correct, region_only_correct) to render this chart.**
 * *Mandatory Requirement*: The figure caption MUST explicitly state the implication of the 'region_only_correct' bar for the paper's main claim (e.g., "This bar represents the rate of Attribution Hallucination, demonstrating that standard accuracy overestimates truthfulness by ignoring spatial context").

3. **Figure 3: Dataset Integrity & Skipped Records**: A pie chart or table showing the distribution of skipped records by reason (e.g., missing bbox, missing image) and the total `skipped_count`.
 * *Source*: `outputs/validation_log.json`. **The research implementation MUST generate these specific breakdowns (skipped reasons) to render this chart.**

## Required Claims

The paper will make the following inferential claims, which the Reference-Validator will verify against the artifacts. **Note: All claims must be supported by specific numerical results from `outputs/evaluation_report.json` or explicitly framed as hypotheses if results are not yet available.**

1. **Claim 1**: "Standard accuracy metrics fail to penalize models that provide correct answers derived from incorrect regions (Attribution Hallucination), leading to an overestimation of model truthfulness."
 * *Verification Requirement*: The claim text MUST include the specific delta found in results (e.g., "Standard Accuracy = X% vs. SAA = Y%").
 * *Data Requirement*: The `outputs/evaluation_report.json` MUST contain a comparative result showing both 'Standard Accuracy' and 'SAA'. **The research plan MUST explicitly include the calculation of Standard Accuracy to support this claim.**

2. **Claim 2**: "The CiteVQA benchmark can be successfully reproduced on free-tier CPU hardware (<7 GB RAM) using quantized models and streaming data loaders."
 * *Verification Requirement*: The claim is supported by the successful execution of `infer/run.py` in the CI logs and the memory usage metrics.
 * *Data Requirement*: The `outputs/evaluation_report.json` (primary research result) MUST contain the actual peak memory usage value (e.g., '6.2 GB') to substantiate the '<7 GB' claim. Relying solely on a separate documentation file is insufficient.

3. **Claim 3**: "Roughly [INSERT_SPECIFIC_VALUE]% of 'correct' answers in the CiteVQA subset are actually attribution hallucinations, indicating a significant WYSIATI bias in current MLLMs."
 * *Verification Requirement*: The specific percentage must be derived from the ratio of `region_only_correct` (or `answer_only_correct` depending on definition) to total correct answers in `outputs/evaluation_report.json`.
 * *Data Requirement*: The claim text MUST be replaced with the actual calculated value (e.g., '[deferred]') OR explicitly defined as a range and confidence interval (e.g., '32% to 36% (95% CI)'). If the research has not produced this number, the claim MUST be explicitly framed as a hypothesis (e.g., "We hypothesize that roughly X%...") rather than a definitive statement with a placeholder.

## Edge Cases (Paper Specific)

- **Ambiguous Bounding Boxes**: If the dataset contains records with ambiguous or missing ground-truth bounding boxes, the paper MUST explicitly report the number of excluded samples and justify their exclusion to maintain metric validity.
- **Repetition of Content**: If the "Results" section risks repeating the "Methods" section's description of the SAA formula, the paper MUST focus the Results section on the *observed values* and *statistical trends* rather than re-defining the metric.

## Requirements

### Functional Requirements

- **FR-001**: The paper MUST describe the exact execution of `infer/run.py` and `eval/run.py` to generate `outputs/infer_results.jsonl` and `outputs/evaluation_report.json`.
- **FR-002**: The paper MUST explicitly define and report the `attribution_hallucination_rate` as a primary metric, distinguishing it from standard accuracy.
- **FR-003**: The paper MUST document the dataset validation process (`data/validate_dataset.py`) and report the `skipped_count` and reasons for exclusion.
- **FR-004**: The paper MUST include a reproducibility appendix detailing the CPU-only environment setup, memory constraints, and random seed configuration.
- **FR-005**: The paper MUST present the error breakdown (Answer Correct/Region Wrong vs. Answer Wrong) to support the WYSIATI bias argument.
- **FR-006**: The paper MUST reference the specific IoU threshold used for the SAA calculation and justify its selection based on the CiteVQA paper.

### Key Entities

- **InferenceResult**: The prediction artifact containing question, predicted answer, and predicted bounding box (from `outputs/infer_results.jsonl`).
- **GroundTruth**: The dataset record containing the correct answer and verified ground-truth bounding box.
- **EvaluationReport**: The final summary artifact containing the SAA score, error breakdown, and skipped count (from `outputs/evaluation_report.json`).
- **ValidationLog**: The log of skipped records and reasons (from `outputs/validation_log.json`).

## Success Criteria

### Measurable Outcomes

- **SC-001**: **Reproducibility Success**: The paper's reproducibility appendix must enable an independent researcher to regenerate the `outputs/evaluation_report.json` with an SAA score within ±0.01 of the reported value.
- **SC-002**: **Metric Validity**: The reported `attribution_hallucination_rate` must be explicitly calculated from the `region_only_correct` (or `answer_only_correct` depending on definition) count in the evaluation report.
- **SC-003**: **Data Integrity Transparency**: The paper must report the exact `skipped_count` and the percentage of the dataset excluded due to missing fields (e.g., missing bbox).
- **SC-004**: **Bias Mitigation Evidence**: The paper must demonstrate that the SAA metric yields a significantly lower score than standard accuracy when Attribution Hallucinations are present, validating the metric's utility.
- **SC-005**: **CPU Feasibility**: The paper must confirm that the entire pipeline (inference + evaluation) completed within the documented time and memory constraints on a CPU-only runner.

## Assumptions

- **Assumption about compute environment**: The paper assumes that the "free-tier CPU runner" environment described in the research phase is representative of a standard, accessible research workstation.
- **Assumption about dataset quality**: The paper assumes that the CiteVQA dataset, after filtering for missing fields, is a valid and representative sample of the benchmark's intended scope.
- **Assumption about model behavior**: The paper assumes that the quantized MLLM model behaves consistently with the full-precision model regarding the *pattern* of errors (even if absolute accuracy varies slightly), making the bias analysis valid.
- **Assumption about IoU threshold**: The paper assumes the community-standard IoU threshold (e.g., 0.5) is the appropriate baseline for defining "correct" regions, as per the original CiteVQA methodology.
- **Assumption about random seeds**: The paper assumes that fixing the random seed in the inference pipeline is sufficient to eliminate non-determinism in the reported SAA score for reproducibility purposes.