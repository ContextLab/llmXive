# Feature Specification: llmXive follow-up: extending "CiteVQA"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document In"

## User Scenarios & Testing

### User Story 1 - Text-Only Retrieval and Reasoning Pipeline (Priority: P1)

The system MUST implement a two-stage pipeline where a small, text-only language model (Phi-3-mini) receives a query and retrieved text chunks to generate an answer and a predicted source chunk ID, entirely without visual input.

**Why this priority**: This is the core hypothesis test. If the text-only model cannot even retrieve the correct text context or generate the answer without visual pre-training, the subsequent spatial grounding analysis is moot. It establishes the baseline "text-reasoning" capability.

**Independent Test**: The pipeline can be fully tested by feeding the system a query and the pre-processed text-only JSON from the CiteVQA dataset, verifying that it outputs a text answer and a chunk ID without crashing or requiring GPU resources.

**Acceptance Scenarios**:

1. **Given** the CiteVQA dataset is pre-processed into text chunks with unique IDs, **When** the system processes a query using the `all-MiniLM-L6-v2` retriever and the Phi-3-mini model, **Then** the system outputs a text answer and a predicted chunk ID within 60 seconds per query.
2. **Given** a query where the answer is present in the top-3 retrieved chunks, **When** the text-only model processes the context, **Then** the model generates an answer that matches the ground truth (exact match or semantic similarity > 0.85) at least 80% of the time.

---

### User Story 2 - Cross-Modal Spatial Grounding Evaluation (Priority: P2)

The system MUST evaluate the "Strict Attributed Accuracy" (SAA) by mapping the predicted chunk ID from the text-only model to its ground-truth bounding box and calculating the Intersection over Union (IoU) against the dataset's annotated bounding box.

**Why this priority**: This directly addresses the research question regarding whether text-only models can perform cross-modal alignment. It quantifies the failure mode (attribution hallucination) by measuring the spatial discrepancy.

**Independent Test**: The evaluation can be tested independently by taking a set of predicted chunk IDs and their corresponding ground-truth coordinates, calculating the IoU, and verifying that the SAA metric is computed correctly regardless of the model's internal reasoning.

**Acceptance Scenarios**:

1. **Given** a predicted chunk ID and its associated ground-truth bounding box coordinates, **When** the system generates the cropped image region and calculates the IoU with the ground truth, **Then** the system reports an SAA score where IoU > 0.5 is required for a "correct" attribution.
2. **Given** a set of 100 queries, **When** the system computes the SAA, **Then** the system outputs a summary statistic (mean SAA) and a distribution plot showing the frequency of high-IoU vs. low-IoU attributions.

---

### User Story 3 - Visual-Only Control Experiment (Priority: P3)

The system MUST execute a control experiment where a separate small model receives only the cropped image of the ground-truth region (without text context) to determine if visual context alone can drive correct attribution.

**Why this priority**: This isolates the modality gap. It helps determine if the failure in User Story 2 is due to a lack of visual pre-training or a fundamental inability to reason about layout from text alone.

**Independent Test**: The control can be tested by feeding the system only image crops (derived from the dataset) and verifying that the model attempts to generate an answer or attribution based solely on visual features.

**Acceptance Scenarios**:

1. **Given** a cropped image of a document region containing the answer, **When** the system passes this image to a small vision-capable model without any text context, **Then** the system records the model's output and compares it to the ground truth answer.
2. **Given** the results of the Visual-Only control, **When** compared against the Text-Only results, **Then** the system generates a comparative report highlighting the performance delta between the two modalities.

---

### Edge Cases

- **What happens when** the text-only model predicts a chunk ID that does not exist in the pre-processed JSON? The system MUST log the error and assign an IoU of 0.0 for that instance.
- **How does the system handle** PDFs where the extracted text layout is corrupted or bounding boxes are malformed? The system MUST skip these specific QA pairs and report the count of skipped items in the final summary.
- **What happens when** the semantic similarity score for the answer is exactly 0.85? The system MUST treat this as a pass (>= 0.85).

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a text-retrieval stage using `all-MiniLM-L6-v2` to encode chunks and retrieve the top-k relevant chunks for a given query (See US-1).
- **FR-002**: System MUST execute a reasoning stage using a CPU-tractable, instruction-tuned small language model (e.g., Phi-3-mini) to generate an answer and a predicted chunk ID from the retrieved text (See US-1).
- **FR-003**: System MUST map the predicted chunk ID to its corresponding bounding box coordinates from the pre-processed JSON and calculate the Intersection over Union (IoU) against the ground-truth box (See US-2).
- **FR-004**: System MUST compute the Strict Attributed Accuracy (SAA) metric, defined as the intersection of answer correctness (semantic similarity >= 0.85) and spatial correctness (IoU > 0.5) (See US-2).
- **FR-005**: System MUST execute a visual-only control experiment where a model receives only the cropped image region of the ground truth to assess visual grounding capability in isolation (See US-3).
- **FR-006**: System MUST perform a paired t-test comparing the SAA scores of the text-only decomposed pipeline against the baseline MLLM scores reported in the original CiteVQA paper to determine statistical significance (p < 0.05) (See US-2).

### Key Entities

- **CiteVQA Question**: A natural language query associated with a specific document page and ground-truth bounding box.
- **Text Chunk**: A segment of extracted text from a PDF, associated with a unique ID and bounding box coordinates.
- **Prediction**: The output of the text-only model, consisting of a generated answer and a predicted chunk ID.
- **Attribution Score**: A binary value (1 for success, 0 for failure) derived from the SAA calculation for a single QA pair.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The Strict Attributed Accuracy (SAA) of the text-only pipeline is measured against the baseline MLLM SAA reported in the original CiteVQA paper to determine the performance gap (See US-2).
- **SC-002**: The statistical significance of the performance difference is measured using a paired t-test with a significance threshold of p < 0.05 against the null hypothesis that there is no difference (See US-2).
- **SC-003**: The failure rate due to "Attribution Hallucination" (correct answer, incorrect box) is measured against the total number of correct answers to quantify the specific contribution of spatial reasoning failure (See US-2).
- **SC-004**: The computational feasibility is measured against the constraint of running on a CPU-only GitHub Actions runner with <= 7 GB RAM and <= 6 hours total runtime (See FR-002, FR-005).
- **SC-005**: The validity of the visual-only control is measured by comparing the model's ability to answer the query from an image crop alone versus from text, isolating the modality contribution (See US-3).

## Assumptions

- The CiteVQA dataset (711 PDFs, a substantial collection of QA pairs) is available and accessible via the official repository without requiring special authentication or paid access.
- The `pdfplumber` library successfully extracts text and bounding box coordinates from all PDFs in the CiteVQA dataset without significant corruption or layout errors.
- The Phi-mini model (quantized to 4-bit) fits within the 7 GB RAM constraint of the GitHub Actions free-tier runner and can complete inference within the 6-hour total job limit for the full dataset.
- The ground-truth bounding boxes in the CiteVQA dataset are accurate and independent of the model's predictions, ensuring no circular validation.
- The semantic similarity threshold of 0.85 (using standard sentence-transformers metrics) is an appropriate community-standard default for "answer correctness" in this domain.
- The original CiteVQA paper provides sufficient baseline SAA scores to serve as a reference for the paired t-test comparison.
- The `all-MiniLM-L6-v2` model is sufficient for retrieving the correct context for the majority of queries in the CiteVQA dataset.
