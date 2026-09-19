# Feature Specification: llmXive follow-up: extending "Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models"

**Feature Branch**: `001-blind-spots-order-analysis`  
**Created**: 2026-08-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models'"

## User Scenarios & Testing

### User Story 1 - Dataset Acquisition and Pre-filtering (Priority: P1)

The research pipeline MUST successfully download the *Blind-Spots-Bench* dataset from the source linked in the primary paper and filter the dataset to retain only "Abstract Reasoning" and "Object-Centric" sub-tasks. This is the foundational step; without the correct subset of data, no analysis of failure modes can occur.

**Why this priority**: This is the data ingestion layer. If the dataset cannot be acquired or filtered correctly, the entire downstream analysis (parsing, classification, statistics) is impossible. It is the single point of failure for data availability.

**Independent Test**: Can be fully tested by running the data acquisition script and verifying the output file contains exactly the expected number of records for the two target sub-tasks, with no records from other categories.

**Acceptance Scenarios**:

1. **Given** the primary paper URL is accessible, **When** the acquisition script executes, **Then** the dataset (total raw count) is downloaded to the local workspace.
2. **Given** the raw dataset is loaded, **When** the filter logic runs for "Abstract Reasoning" and "Object-Centric", **Then** the output file contains only records matching these two categories, and the count equals the number of available matching records in the source.
3. **Given** the filtered dataset, **When** the script validates the file integrity, **Then** the system reports 0 corrupted or missing fields required for the next step.

---

### User Story 2 - CoT Trace Generation and Parsing (Priority: P2)

The system MUST execute a mid-sized open-weight LLM (e.g., Llama-3-8B-Int4 or Mistral-7B-Int4) on the filtered tasks using a fixed temperature (0.0) to generate Chain-of-Thought (CoT) traces, and subsequently parse these traces to identify the first mention and the last mention of the task's explicit constraint, including semantic equivalence checks.

**Why this priority**: This step generates the primary signal (the reasoning trace) and extracts the specific temporal markers (first/last mention) required to classify errors. It is the core computational engine of the research.

**Independent Test**: Can be fully tested by running the generation script on a small sample (e.g., 5 tasks), verifying the model outputs a CoT trace for each, and confirming the parser correctly identifies the start and end indices of the constraint string (or semantic equivalent) within those traces.

**Acceptance Scenarios**:

1. **Given** a filtered task input, **When** the LLM inference script runs with temperature 0.0, **Then** a complete CoT trace is generated within 10 minutes per task.
2. **Given** a generated CoT trace, **When** the parsing script runs, **Then** it outputs the character offset of the first constraint mention and the last constraint mention, or a semantic match flag if the constraint was paraphrased.
3. **Given** a task where the constraint is never mentioned (and no semantic match is found), **When** the parser runs, **Then** it returns a null or specific "not found" flag for both start and end positions.

---

### User Story 3 - Error Classification and Statistical Analysis (Priority: P3)

The system MUST apply a rule-based classifier to label each trace as *Perceptual Error*, *Procedural Error*, or *Correct*, and then compute the proportion of each error type per task category, followed by a Chi-squared (or Fisher's exact) test to determine statistical association.

**Why this priority**: This is the analytical conclusion. It transforms raw data into the research findings (the distribution of error types) and validates the hypothesis regarding task-dependence.

**Independent Test**: Can be fully tested by providing a small, hand-labeled test set of traces to the classifier, verifying the labels match the ground truth, and confirming the statistical test returns a p-value and association statistic.

**Acceptance Scenarios**:

1. **Given** a trace where the constraint is missing in the first step (and no semantic match), **When** the classifier runs, **Then** the trace is labeled "Perceptual Error".
2. **Given** a trace where the constraint appears in the first step but is missing in the final step, **When** the classifier runs, **Then** the trace is labeled "Procedural Error".
3. **Given** the labeled dataset of ≥ 50 samples, **When** the statistical analysis runs, **Then** it outputs a contingency table and a p-value indicating whether error type distribution is associated with task category.

### Edge Cases

- What happens when the LLM generation times out or produces an empty response? (System MUST log the error, skip the trace, and not crash).
- How does the system handle cases where the constraint string appears as a substring within a different word (false positive match)? (The parser MUST use word-boundary matching or exact phrase matching).
- What if the number of samples in a category is too small (< 5) for a Chi-squared test? (System MUST automatically switch to Fisher's exact test).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download the *Blind-Spots-Bench* dataset from the arXiv source link and filter it to retain only "Abstract Reasoning" and "Object-Centric" sub-tasks (See US-1).
- **FR-002**: System MUST execute a mid-sized open-weight LLM (e.g., Llama-3-8B-Int4, Mistral-7B-Int4) on the filtered tasks using temperature 0.0 to ensure deterministic CoT generation (See US-2).
- **FR-003**: System MUST parse generated CoT traces to identify the character offset of the first and last occurrence of the task's explicit constraint, or a semantic equivalent (See US-2).
- **FR-004**: System MUST classify each trace as *Perceptual Error*, *Procedural Error*, or *Correct* based on the presence/absence of the constraint in the first and last steps (See US-3).
- **FR-005**: System MUST compute the proportion of each error type per task category and perform a Chi-squared or Fisher's exact test to determine statistical significance (See US-3).
- **FR-006**: System MUST explicitly check for the presence of the 'constraint' field in every task record upon ingestion. If any record in the 'Abstract Reasoning' or 'Object-Centric' subsets lacks this field, the system MUST halt execution, log the specific missing record IDs, and report a 'Dataset Integrity Error' with a count of missing constraints (See US-1).
- **FR-007**: System MUST frame the statistical findings as associational (correlation between task category and error type) rather than causal, as the design is observational (See US-3).
- **FR-008**: System MUST implement a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) if >1 hypothesis test is performed across sub-categories to control family-wise error rate (See US-3).
- **FR-009**: System MUST ensure all computations (model inference, parsing, statistics) complete within 6 hours on a CPU-only runner with ≤ 7 GB RAM, using a 4-bit quantized model if necessary (See US-2).
- **FR-010**: System MUST validate the error classification by sampling [deferred] of traces and comparing the automated labels against human expert annotation (or a separate rule-based oracle) to ensure the 'Perceptual/Procedural' distinction is not a trivial restatement of the text (See US-3).
- **FR-011**: System MUST implement a semantic equivalence check using a lightweight embedding model (e.g., all-MiniLM-L6-v2) to detect paraphrased constraints, preventing false 'Perceptual Errors' when the model rephrases the constraint (See US-2).
- **FR-012**: System MUST skip any individual task inference that exceeds 10 minutes to ensure the global 6-hour runtime limit is not exceeded (See US-2).

### Key Entities

- **Task Record**: Represents a single item from *Blind-Spots-Bench*, containing the prompt, the explicit constraint string, and the task category.
- **CoT Trace**: The text output generated by the LLM, containing the reasoning steps.
- **Error Label**: The classification result (Perceptual, Procedural, Correct) derived from the trace analysis.
- **Statistical Result**: The output of the hypothesis test (p-value, test statistic, contingency table).

## Success Criteria

### Measurable Outcomes

- **SC-001**: The proportion of *Perceptual Errors* in "Abstract Reasoning" and "Object-Centric" tasks is measured against the statistical significance threshold (p < 0.05) to determine if error distribution is task-dependent (See FR-005).
- **SC-002**: The p-value from the Chi-squared/Fisher's exact test is measured against the significance threshold (α = 0.05) to determine if error distribution is task-dependent (See FR-005).
- **SC-003**: The total runtime of the end-to-end analysis (download to stats) is measured against the CI time limit. (See FR-009).
- **SC-004**: The memory peak usage of the LLM inference and parsing pipeline is measured against a fixed RAM constraint. (See FR-009).
- **SC-005**: The consistency of the error classification is measured by re-running the parser on a fixed sample; the label agreement rate must be ≥ 99% (deterministic) (See FR-004).
- **SC-006**: The accuracy of the automated error classification is measured against the human expert sample; the agreement rate must be ≥ 85% to validate the methodology (See FR-010).

## Assumptions

- The *Blind-Spots-Bench* dataset (arXiv:2607.08317) contains explicit, parseable constraint strings for every task in the "Abstract Reasoning" and "Object-Centric" categories.
- Mid-sized open-weight models (4-bit quantized) can be loaded and run inference on a CPU-only GitHub Actions runner within the time limit for a representative sample of tasks.
- The "constraint" mentioned in the task description is a unique string that can be reliably located within the generated text using standard string matching or semantic embedding.
- The research design is observational; therefore, no causal claims regarding the "order of reasoning steps" causing the error will be made, only associational findings. This is a necessary constraint of the available dataset, and the research question has been reframed accordingly.
- The statistical power of the test is limited by the available sample size.; a power analysis is deferred, but the study acknowledges this limitation in the final report.
- The "Abstract Reasoning" and "Object-Centric" sub-tasks are distinct categories in the dataset metadata and can be filtered programmatically without ambiguity.
- A 4-bit quantized model is sufficient to run within 7GB RAM on a standard CPU runner.
- A reasonable per-task timeout is sufficient to generate a valid CoT trace for the selected model and task complexity.