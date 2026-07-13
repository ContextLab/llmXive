# Feature Specification: llmXive follow-up: extending "CiteVQA"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document In"

## User Scenarios & Testing

### User Story 1 - Text-Only Retrieval and Reasoning Pipeline (Priority: P1)

The system MUST implement a two-stage pipeline where a small, text-only language model (Phi-3-mini) receives a query and retrieved text chunks to generate an answer and a predicted source chunk ID, entirely without visual input. The evaluation MUST be performed on a held-out test set ([deferred] of the dataset) that was strictly excluded from any fine-tuning or training data to ensure zero-shot generalization.

**Why this priority**: This is the core hypothesis test. If the text-only model cannot even retrieve the correct text context or generate the answer without visual pre-training, the subsequent spatial grounding analysis is moot. It establishes the baseline "text-reasoning" capability.

**Independent Test**: The pipeline can be fully tested by feeding the system a query and the pre-processed text-only JSON from the CiteVQA dataset, verifying that it outputs a text answer and a chunk ID without crashing or requiring GPU resources.

**Acceptance Scenarios**:

1. **Given** the CiteVQA dataset is pre-processed into text chunks with unique IDs, **When** the system processes a query using the `all-MiniLM-L6-v2` retriever and the Phi-3-mini model, **Then** the system outputs a text answer and a predicted chunk ID within 60 seconds per query.
2. **Given** a query where the answer is present in the top-3 retrieved chunks, **When** the text-only model processes the context, **Then** the model generates an answer that matches the ground truth (Exact Match OR semantic similarity >= 0.85 using `sentence-transformers/all-MiniLM-L6-v2` with L2 normalization) at least 80% of the time.

---

### User Story 2 - Cross-Modal Spatial Grounding Evaluation (Priority: P2)

The system MUST evaluate the "Strict Attributed Accuracy" (SAA) by mapping the predicted chunk ID from the text-only model to its ground-truth bounding box and calculating the Intersection over Union (IoU) against the dataset's annotated bounding box. The mapping logic MUST be deterministic: the predicted chunk ID maps to the *exact* bounding box stored in the pre-processed JSON. If the ID is missing, IoU is 0.0.

**Why this priority**: This directly addresses the research question regarding whether text-only models can perform cross-modal alignment. It quantifies the failure mode (attribution hallucination) by measuring the spatial discrepancy.

**Independent Test**: The evaluation can be tested independently by taking a set of predicted chunk IDs and their corresponding ground-truth coordinates, calculating the IoU, and verifying that the SAA metric is computed correctly regardless of the model's internal reasoning.

**Acceptance Scenarios**:

1. **Given** a predicted chunk ID and its associated ground-truth bounding box coordinates from the pre-processed JSON, **When** the system generates the cropped image region based on the mapped box and calculates the IoU with the ground truth, **Then** the system reports an SAA score where IoU > 0.5 is required for a "correct" attribution.
2. **Given** a set of 100 queries, **When** the system computes the SAA, **Then** the system outputs a summary statistic (mean SAA) and a distribution plot showing the frequency of high-IoU vs. low-IoU attributions.

---

### User Story 3 - Visual-Only Localization Control Experiment (Priority: P3)

The system MUST execute a control experiment where a vision-capable model receives only the full-page image (without text context) and MUST predict a bounding box (or chunk ID) for the answer location. The system then calculates SAA based on this *predicted* location against the ground truth. This tests if the model can *localize* the answer visually.

**Why this priority**: This isolates the modality gap. It helps determine if the failure in User Story 2 is due to a lack of visual pre-training or a fundamental inability to reason about layout from text alone. The original design (feeding the ground-truth crop) failed to test localization; this revised design tests it directly.

**Independent Test**: The control can be tested by feeding the system only full-page images and verifying that the model attempts to generate a bounding box or chunk ID based solely on visual features.

**Acceptance Scenarios**:

1. **Given** a full-page image containing the answer, **When** the system passes this image to a small vision-capable model without any text context, **Then** the system records the model's predicted bounding box (or chunk ID) and compares it to the ground truth location.
2. **Given** the results of the Visual-Only localization control, **When** compared against the Text-Only results, **Then** the system generates a comparative report highlighting the performance delta between the two modalities.

---

### Edge Cases

- **What happens when** the text-only model predicts a chunk ID that does not exist in the pre-processed JSON? The system MUST log the error and assign an IoU of 0.0 for that instance.
- **How does the system handle** PDFs where the extracted text layout is corrupted or bounding boxes are malformed? The system MUST skip these specific QA pairs and report the count of skipped items in the final summary.
- **What happens when** the semantic similarity score for the answer is exactly 0.85? The system MUST treat this as a pass (>= 0.85).

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a text-retrieval stage using `all-MiniLM-L6-v2` to encode chunks and retrieve the top-k relevant chunks for a given query (See US-1).
- **FR-002**: System MUST execute a reasoning stage using a CPU-tractable, instruction-tuned small language model (e.g., Phi-3-mini) to generate an answer and a predicted chunk ID from the retrieved text. The model MUST be evaluated on a held-out test set ([deferred] of data) strictly excluded from training to ensure zero-shot capability (See US-1).
- **FR-003**: System MUST map the predicted chunk ID to its corresponding bounding box coordinates from the pre-processed JSON and calculate the Intersection over Union (IoU) against the ground-truth box. If the ID is missing, IoU MUST be 0.0 (See US-2).
- **FR-004**: System MUST compute the Strict Attributed Accuracy (SAA) metric, defined as the intersection of answer correctness (Exact Match OR semantic similarity >= 0.85 using `sentence-transformers/all-MiniLM-L6-v2` with L2 normalization) and spatial correctness (IoU > 0.5) (See US-2).
- **FR-005**: System MUST execute a visual-only localization control experiment where a model receives only the full-page image (no text) and MUST predict a bounding box (or chunk ID) for the answer location. The system MUST then calculate SAA based on this prediction (See US-3).
- **FR-006**: System MUST embed the baseline MLLM SAA scores reported in the original CiteVQA paper as a fixed, immutable JSON reference within the system's data layer (See US-2).
- **FR-007**: System MUST perform a one-sample t-test comparing the mean SAA scores of the text-only pipeline against the fixed scalar baseline (from FR-006) to determine statistical significance (p < 0.05) (See US-2).

### Key Entities

- **CiteVQA Question**: A natural language query associated with a specific document page and ground-truth bounding box.
- **Text Chunk**: A segment of extracted text from a PDF, associated with a unique ID and bounding box coordinates.
- **Prediction**: The output of the text-only model, consisting of a generated answer and a predicted chunk ID.
- **Attribution Score**: A binary value (1 for success, 0 for failure) derived from the SAA calculation for a single QA pair.
- **Baseline Reference**: A fixed JSON object containing the scalar SAA mean from the original CiteVQA paper, embedded in the system code.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The Strict Attributed Accuracy (SAA) of the text-only pipeline is measured against the baseline MLLM SAA (from FR-006) to determine the performance gap (See US-2).
- **SC-002**: The statistical significance of the performance difference is measured using a one-sample t-test with a significance threshold of p < 0.05 against the null hypothesis that the new mean equals the baseline mean (See FR-007).
- **SC-003**: The failure rate due to "Attribution Hallucination" (correct answer, incorrect box) is measured against the total number of correct answers to quantify the specific contribution of spatial reasoning failure (See US-2).
- **SC-004**: The system MUST complete inference on the full held-out test set within 6 hours on a standard GitHub Actions runner (<= 7 GB RAM). The system MUST report the total runtime, and the test fails if runtime > 6 hours (See FR-002).
- **SC-005**: The validity of the visual-only localization control is measured by comparing the model's ability to predict the correct location from an image alone versus from text, isolating the modality contribution (See US-3).

## Assumptions

- The CiteVQA dataset (a substantial collection of QA pairs) is available and accessible via the official repository without requiring special authentication or paid access.
- The `pdfplumber` library successfully extracts text and bounding box coordinates from all PDFs in the CiteVQA dataset without significant corruption or layout errors.
- The Phi-mini model (quantized to 4-bit) fits within the 7 GB RAM constraint of the GitHub Actions free-tier runner and can complete inference within the 6-hour total job limit for the full dataset.
- The ground-truth bounding boxes in the CiteVQA dataset are accurate and independent of the model's predictions, ensuring no circular validation.
- The semantic similarity threshold of 0.85 (using `sentence-transformers/all-MiniLM-L6-v2` with L2 normalization) is an appropriate community-standard default for "answer correctness" in this domain.
- The original CiteVQA paper provides a scalar SAA mean that can be embedded as a fixed baseline reference.
- The `all-MiniLM-L6-v2` model is sufficient for retrieving the correct context for the majority of queries in the CiteVQA dataset.
- The dataset can be split into an [deferred] training/validation set and a [deferred] held-out test set for zero-shot evaluation without compromising statistical power.