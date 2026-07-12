# Feature Specification: llmXive Follow-up: Extending EnterpriseClawBench

**Feature Branch**: `001-llmxive-extend-enterprisecrclawbench`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'EnterpriseClawBench: Benchmarking Agents from Real Workplace Sessions'"

## User Scenarios & Testing

### User Story 1 - Syntactic & Pragmatic Feature Extraction (Priority: P1)

**Journey**: The researcher needs to process the raw EnterpriseClawBench execution logs to automatically extract and categorize specific structural linguistic features (syntax tree depth, token frequency, pragmatic markers) for both failed and successful tool-call sequences.

**Why this priority**: This is the foundational data preparation step. Without accurate, labeled structural features distinguishing failure from success, no subsequent analysis or model training can occur. It directly addresses the "What specific syntactic and pragmatic features..." part of the research question.

**Independent Test**: The system can be tested by running the extraction pipeline on a small, manually verified subset of traces and confirming that the output JSON contains the correct feature vectors and labels (Success/Failure) for each trace.

**Acceptance Scenarios**:

1. **Given** a raw execution log file from the EnterpriseClawBench dataset, **When** the extraction module parses the log, **Then** it must output a structured record containing the calculated syntax tree depth, token frequency distribution, and identified pragmatic markers (e.g., error recovery attempts).
2. **Given** a trace identified as "failed" in the ground truth, **When** features are extracted, **Then** the output record must be labeled with the `status: failed` flag and include the specific pragmatic markers associated with failure (e.g., state transition errors).
3. **Given** a trace identified as "successful" in the ground truth, **When** features are extracted, **Then** the output record must be labeled with the `status: success` flag and show the absence of specific failure-associated pragmatic markers.

---

### User Story 2 - Lightweight Adapter Training & Feasibility Prediction (Priority: P2)

**Journey**: The researcher needs to train a CPU-optimized sequence-to-sequence model on the extracted feature triplets to predict whether a specific failure mode is correctable via syntax rewriting or requires full model retraining. The ground truth for "correctable" is derived independently from manual expert annotation or a separate rule-based oracle, not from the syntactic features themselves.

**Why this priority**: This addresses the core "to what extent can these features predict..." aspect of the research question. It moves from observation to prediction, determining the feasibility of the proposed lightweight intervention.

**Independent Test**: The training pipeline can be tested independently by running it on a fixed training split and verifying that the loss converges and the model produces a binary classification (Correctable vs. Unfixable) with a measurable accuracy on a held-out validation set.

**Acceptance Scenarios**:

1. **Given** the constructed triplet dataset (System Prompt, Failed_Trace_Structure, Successful_Correction_Structure), **When** the adapter training process completes, **Then** the model must output a binary prediction for each test sample indicating whether the failure is "syntactically correctable" or "requires retraining."
2. **Given** a set of known "correctable" failure cases in the validation set, **When** the model processes them, **Then** the prediction accuracy for the "correctable" class must exceed the random baseline (e.g., >50% for a binary task) to demonstrate predictive capability.
3. **Given** the computational constraints (7GB RAM, 2 CPU cores), **When** the training job runs, **Then** the process must complete without triggering an Out-Of-Memory (OOM) error or exceeding the 6-hour time limit.

---

### User Story 3 - Artifact Delivery Score Evaluation (Priority: P3)

**Journey**: The researcher needs to evaluate the end-to-end impact of the trained adapter by measuring the "Artifact Delivery Score" on the held-out Lite set, comparing the baseline performance against the adapter-enhanced system. The adapter learns a generalizable correction policy based on abstract fix representations, not raw successful traces.

**Why this priority**: This validates the practical utility of the research. It answers whether the linguistic intervention actually improves the outcome (artifact delivery) in the restrictive enterprise environment.

**Independent Test**: The evaluation can be tested by running the baseline and adapter-enhanced configurations on a representative multi-task Lite set and comparing the resulting scores using a statistical test to confirm significance.

**Acceptance Scenarios**:

1. **Given** the held-out 120-task Lite set and the baseline "Model + Harness" configuration, **When** the evaluation runs, **Then** it must record the Artifact Delivery Score for each task.
2. **Given** the same 120-task Lite set and the "Model + Adapter + Harness" configuration, **When** the evaluation runs, **Then** it must record the Artifact Delivery Score for each task and log the total runtime latency.
3. **Given** the paired scores from the baseline and adapter-enhanced runs, **When** the statistical analysis (paired t-test or Wilcoxon signed-rank) is applied, **Then** the system must output a p-value to determine if the improvement is statistically significant (p < 0.05).

---

### Edge Cases

- **What happens when a trace contains ambiguous pragmatic markers?** The system must default to a "neutral" classification or flag the trace for manual review, rather than forcing a binary success/failure label that could skew training.
- **How does the system handle traces that are too large for the 7GB RAM limit?** The pipeline must implement a streaming or chunking strategy to process large logs without loading the entire file into memory at once.
- **What happens if the adapter training loss does not converge?** The system must trigger a fallback to a simpler heuristic model (e.g., rule-based syntax correction) to ensure the evaluation step can still proceed, while logging the failure for analysis.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse raw execution logs to extract syntax tree depth, token frequency distributions, and pragmatic markers (e.g., error recovery attempts) for every trace in the EnterpriseClawBench dataset (See US-1).
- **FR-002**: System MUST construct a triplet dataset consisting of `(System_Prompt, Failed_Trace_Structure, Successful_Correction_Structure)` where `Successful_Correction_Structure` is extracted from the corresponding successful trace in the dataset for the same task, and the "correctable" label is derived from manual expert annotation or a separate rule-based oracle (See US-2).
- **FR-003**: System MUST train a distilled T5-small (≤60M parameters) sequence-to-sequence model to predict correction feasibility without requiring GPU acceleration or 8-bit quantization libraries (See US-2).
- **FR-004**: System MUST implement an evaluation pipeline that runs the "Model + Adapter + Harness" configuration on the 120-task held-out Lite set and calculates the Artifact Delivery Score, ensuring the adapter learns a generalizable correction policy based on abstract fix representations (See US-3).
- **FR-005**: System MUST apply a statistical significance test (paired t-test or Wilcoxon signed-rank) to compare the baseline and adapter-enhanced Artifact Delivery Scores, reporting the p-value (See US-3).
- **FR-006**: System MUST log peak RSS memory (via /proc/self/status) and wall-clock time (start to end of training) to verify compliance with the 7GB RAM and 6-hour time limit constraints (See US-2).

### Key Entities

- **Execution Trace**: A log of tool-call sequences from an agent session, containing raw tokens, error states, and outcome labels.
- **Feature Vector**: A structured representation of a trace containing numerical and categorical values for syntax depth, token frequency, and pragmatic markers.
- **Correction Triplet**: A training sample linking a failed trace structure to its corresponding successful correction structure.
- **Adapter Model**: The lightweight sequence-to-sequence model trained to predict correction feasibility.
- **Artifact Delivery Score**: The primary metric measuring the success of an agent session in delivering the required output.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The distinctiveness of syntactic and pragmatic markers between failed and successful traces is measured against the distribution differences using non-parametric tests (Mann-Whitney U) with Bonferroni or Benjamini-Hochberg FDR correction (See US-1).
- **SC-002**: The predictive accuracy of the adapter for "correctable" vs. "unfixable" failures is measured against the ground truth labels in the held-out validation set, with a pass criterion of accuracy ≥ 60% (See US-2).
- **SC-003**: The improvement in Artifact Delivery Score is measured against the baseline "Model + Harness" configuration on the 120-task Lite set (See US-3).
- **SC-004**: The statistical significance of the performance improvement is measured against the threshold of p < 0.05 using a paired statistical test (See US-3).
- **SC-005**: The resource efficiency of the adapter is measured against the constraints of ≤7GB RAM and ≤6 hours total runtime on a CPU-only runner (See US-2).

## Assumptions

- **Dataset Availability**: The EnterpriseClawBench dataset (852 tasks) is publicly accessible and contains the necessary raw execution logs and ground truth labels for "failed" and "successful" sessions.
- **Compute Constraints**: The GitHub Actions free-tier runner (multi-core CPU, standard RAM) is sufficient to train a small, distilled sequence-to-sequence model on the sampled dataset without requiring GPU acceleration.
- **Primary Hypothesis (H1)**: Syntactic and pragmatic features (e.g., syntax tree depth, token frequency) contain sufficient signal to distinguish between failures caused by syntax mismatches and those caused by fundamental reasoning gaps.
- **Fallback Analysis**: If H1 is rejected (features show no distinctiveness, p > 0.05 after correction), the analysis will pivot to a null model baseline and report the lack of signal as a key finding, rather than proceeding with adapter training.
- **Correction Feasibility**: There exists a non-trivial subset of "failed" traces that are "correctable" via syntax rewriting, meaning a null result (all failures are unfixable) is a valid and informative outcome.
- **Statistical Power**: The held-out Lite set provides sufficient statistical power to detect a meaningful difference in Artifact Delivery Scores between the baseline and adapter-enhanced configurations.
- **Inference Framing**: Since the study is observational (analyzing existing traces), all conclusions regarding "feasibility of correction" will be framed as associational predictions rather than causal claims of model capability.
- **Threshold Justification**: Any decision cutoffs used in feature extraction (e.g., defining a "pragmatic marker") will be based on community-standard definitions or will include a sensitivity analysis sweeping the cutoff over a small set (e.g., {0.01, 0.05, 0.1}) to report stability.