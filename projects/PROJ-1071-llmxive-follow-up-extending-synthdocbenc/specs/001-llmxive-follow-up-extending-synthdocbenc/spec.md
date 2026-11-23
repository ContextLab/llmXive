# Feature Specification: llmXive follow-up: extending "SynthDocBench" with Decoupled Retrieval

**Feature Branch**: `001-llmxive-retrieval-extension`  
**Created**: 2026-09-06  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending SynthDocBench to test if decoupling retrieval eliminates middle-third bias"

## User Scenarios & Testing

### User Story 1 - Reproduce Baseline "Middle-Third" Bias (Priority: P1)

The researcher MUST be able to execute the original SynthDocBench evaluation protocol on the static PDF images to reproduce the documented "middle-third" positional bias and establish per-model baseline accuracy.

**Why this priority**: This is the essential control condition. Without a verified baseline showing the bias exists in the static-image setup, any observed changes in the retrieval condition cannot be attributed to the intervention. It validates the environment and the dataset integrity before introducing complexity.

**Independent Test**: Can be fully tested by running the static-image evaluation pipeline on a set of synthetic documents and confirming the accuracy dip in the middle third of the document length distribution matches the expected trend from prior work.

**Acceptance Scenarios**:

1. **Given** the 200 synthetic long documents in static PDF format and the list of 7 VLMs, **When** the system runs the baseline evaluation protocol, **Then** the accuracy for questions in the middle third of the document must be at least 5 percentage points lower than the average accuracy for questions in the first and last thirds.
2. **Given** the baseline results, **When** the researcher inspects the per-model accuracy tables, **Then** a clear degradation pattern correlated with document length and question position must be visible for all tested models.

---

### User Story 2 - Execute Retrieval-Augmented Inference Pipeline (Priority: P2)

The researcher MUST be able to run the two-step inference pipeline where relevant page snippets are retrieved via a CPU-based index and injected into the VLM context alongside the original image.

**Why this priority**: This implements the core hypothesis test. It is the intervention mechanism that decouples retrieval from visual attention. It must function independently of the baseline to isolate the effect of the injected text.

**Independent Test**: Can be tested by selecting a specific "middle-third" question, running the retrieval step to fetch the correct page text, and verifying the VLM receives the image plus the retrieved text snippet before generating an answer.

**Acceptance Scenarios**:

1. **Given** a question targeting the middle third of a document and the OCR text index, **When** the system generates a search query and performs retrieval, **Then** the retrieved snippet MUST contain the ground-truth answer text OR a phrase with a semantic similarity score ≥ 0.85 (measured by cosine similarity of sentence embeddings) to the ground-truth answer.
2. **Given** the retrieved text and the original document image, **When** the VLM processes the combined input, **Then** the system must successfully generate a response without exceeding the 6-hour CI time limit or running out of memory (7 GB RAM).

---

### User Story 3 - Quantify Accuracy Recovery and Correlate with Context Size (Priority: P3)

The researcher MUST be able to compute the accuracy delta between the retrieval-augmented condition and the baseline, and perform a non-parametric correlation analysis between this recovery magnitude and the model's native context window size.

**Why this priority**: This fulfills the specific research question regarding whether the bias is an attentional bottleneck and whether smaller-context models benefit most. It synthesizes the data from US-01 and US-02 into the final scientific claim.

**Independent Test**: Can be tested by running the statistical analysis script on the collected accuracy metrics and verifying the output includes the correlation coefficient and significance value.

**Acceptance Scenarios**:

1. **Given** the baseline accuracy and retrieval-augmented accuracy for the 7 models, **When** the system calculates the delta for "middle-third" questions, **Then** the result must show a positive recovery (improvement) for at least some models if the hypothesis holds.
2. **Given** the recovery deltas and the native context window sizes (4k, 8k, 32k tokens) for each model, **When** the Spearman rank correlation is computed, **Then** the system must output the Spearman r value, p-value, and explicitly classify the relationship as "inverse" if r < -0.3 and p < 0.05, or report "no significant inverse relationship" otherwise.

---

### Edge Cases

- What happens when the OCR process fails to extract text from a specific page (e.g., due to complex layout or low contrast)? The system must handle missing index entries gracefully (e.g., by skipping retrieval for that page or falling back to a default empty string) without crashing the inference pipeline.
- How does the system handle a query that retrieves multiple overlapping snippets? The system must enforce a strict token limit (e.g., ≤ 2048 tokens) for the injected text to prevent context overflow, prioritizing the most relevant snippets based on the retrieval score.
- What if the VLM hallucinates an answer even when the correct text is present in the context? The evaluation metric must strictly compare the generated answer against the ground truth, recording a failure even if the information was available, to accurately measure the model's parsing ability.

## Requirements

### Functional Requirements

- **FR-001**: System MUST generate 200 synthetic long documents with both static PDF images and a parallel OCR-processed text index containing page-level layout metadata (See US-01).
- **FR-002**: System MUST implement a CPU-based retrieval mechanism (e.g., FAISS CPU or keyword/regex matching) that returns relevant text snippets (See US-02).
- **FR-003**: System MUST construct a combined input payload consisting of the original document image and the retrieved text snippets, ensuring the total token count does not exceed the model's native limit (See US-02).
- **FR-004**: System MUST execute the evaluation pipeline for 7 distinct VLMs stratified by native context window size (4k, 8k, 32k tokens) to ensure comparative validity (See US-03).
- **FR-005**: System MUST compute the accuracy delta specifically for "middle-third" questions between the baseline and retrieval-augmented conditions for each model (See US-03).
- **FR-006**: System MUST perform a Spearman rank correlation analysis (or Kruskal-Wallis test if treating context size as categorical) between the magnitude of accuracy recovery and the model's native context window size to test the attentional bottleneck hypothesis (See US-03).
- **FR-007**: System MUST validate the pipeline integrity by measuring performance on "easy" questions (first/last third) to ensure the retrieval mechanism does not degrade performance on well-attended regions (See US-03).
- **FR-008**: System MUST measure and report the retrieval precision (true positives / (true positives + false positives)) and recall (true positives / (true positives + false negatives)) for the retrieval mechanism against the ground-truth answers (See US-02, US-03).

### Key Entities

- **Researcher**: The user role executing the evaluation pipeline, authorized to run baseline and retrieval-augmented tests, inspect logs, and interpret statistical outputs.
- **Synthetic Document**: A generated long-form document containing structured layout, text, and a specific "middle-third" region of interest, existing in both image (PDF) and text (OCR) formats.
- **Retrieval Index**: A CPU-based data structure mapping page coordinates and text content to allow fast lookup of relevant snippets based on a query.
- **Evaluation Metric**: The accuracy score (0.0 to 1.0) of the VLM's answer against the ground truth, computed separately for baseline and retrieval-augmented conditions.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The magnitude of accuracy recovery for "middle-third" questions is measured against the baseline static-image accuracy to determine if the retrieval intervention eliminates the bias (See FR-005, US-03).
- **SC-002**: The Spearman rank correlation coefficient between accuracy recovery and native context window size is measured against the null hypothesis of zero correlation to validate the attentional bottleneck theory (See FR-006, US-03).
- **SC-003**: The false-positive rate of the retrieval mechanism is measured against the total number of retrieval queries; a retrieval is defined as a false positive if the retrieved snippet's semantic similarity to the query is < 0.5 AND it does not contain the ground-truth answer (See FR-008, US-02).
- **SC-004**: The total compute time for the full evaluation pipeline (7 models × 200 docs × 2 conditions) is measured against the 6-hour CI limit to ensure feasibility on free-tier runners (See FR-002, US-02).
- **SC-005**: The memory peak usage during the OCR indexing and retrieval phase is measured against the 7 GB RAM constraint to confirm no GPU/CUDA dependencies are required (See FR-002, US-02).
- **SC-006**: The p95 latency of retrieval queries is measured against a threshold of ≤ 2 seconds per query to ensure the retrieval mechanism does not become a bottleneck (See FR-002, US-02).

## Assumptions

- **Assumption about data validity**: The SynthDocBench generation pipeline can produce 200 documents where the "middle-third" region is consistently defined and the OCR process (Tesseract) can reliably extract text with sufficient accuracy for keyword matching.
- **Assumption about compute constraints**: The selected VLMs can be loaded and run inference on a CPU-only environment (2 cores, 7 GB RAM) within the 6-hour time limit, likely requiring the use of smaller parameter models or quantization that does not require CUDA (e.g., standard float16/32 on CPU).
- **Assumption about correlation direction**: The hypothesis that smaller-context models will show greater recovery is based on the premise that they are more severely impacted by attention dilution, but the study remains open to a null result which would imply the bias is visual, not attentional.
- **Assumption about dataset-variable fit**: The SynthDocBench dataset contains all necessary variables (question text, ground truth answer, page coordinates) to compute the accuracy delta and correlation; no external data sources are required.
- **Assumption about threshold justification**: The definition of "middle-third" (e.g., pages 34-66 of a 100-page doc) is a standard partition used in the original benchmark, and no sensitivity analysis of the boundary is required as the definition is fixed by the benchmark protocol.
- **Assumption about inference framing**: Since the study is observational (no random assignment of models to contexts), any claims about "attentional bottlenecks" will be framed as associational findings derived from the intervention, not causal proofs of the model's internal architecture.