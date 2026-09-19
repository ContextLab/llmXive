# Feature Specification: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

**Feature Branch**: `001-llmxive-layout-distillation`  
**Created**: 2026-09-19  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Scalable Visual Pretraining for Language Intelligence'"

## User Scenarios & Testing

### User Story 1 - Data Ingestion and Latent Target Generation (Priority: P1)

The system must ingest a subset of the scientific document corpus (text + layout annotations) and generate "ground truth" visual layout latents using a frozen, pre-trained visual encoder to serve as distillation targets.

**Why this priority**: This is the foundational step. Without the ground-truth targets derived from the visual modality, the text-only distillation cannot proceed. It validates that the dataset contains the necessary paired information and that the frozen encoder is accessible within the CPU-only constraint (inference only).

**Independent Test**: The pipeline can be run on a representative sample of documents. The test verifies that the output includes the original text and a corresponding embedding vector (latent) for each document, with no errors regarding missing data or encoder loading.

**Acceptance Scenarios**:

1. **Given** a subset of [deferred] scientific documents with text and layout annotations, **When** the ingestion script runs, **Then** it successfully loads the frozen visual encoder and generates a latent embedding for every document without GPU usage.
2. **Given** a document where the text conversion has lost specific layout cues (e.g., image boundaries), **When** the latent is generated, **Then** the embedding reflects the visual structure of the original image, distinct from the text-only representation, defined as a cosine similarity difference ≥ 0.1 or KL divergence ≥ 0.05 compared to a text-only baseline latent.
3. **Given** the dataset contains missing layout annotations for a specific page, **When** the ingestion script runs, **Then** it skips that page and logs a warning, ensuring the training set remains consistent.

---

### User Story 2 - Text-to-Visual Distillation Training (Priority: P2)

The system must train a DistilledModel (a parameter-efficient architecture) to predict the visual layout latents using only the plain text input, minimizing Mean Squared Error (MSE) loss.

**Why this priority**: This is the core research mechanism. It tests the hypothesis that text implicitly encodes structural information. This step must complete within a feasible CPU time limit and under a specified RAM constraint to be feasible.

**Independent Test**: The training script can be executed on a small subset (e.g., 500 documents) to verify convergence of the MSE loss and that the model fits within the memory constraints. The test confirms the model outputs a vector of the correct dimensionality matching the frozen encoder.

**Acceptance Scenarios**:

1. **Given** the text inputs and the generated visual latents, **When** the distillation training starts, **Then** the model converges to an MSE loss at least 5% lower than a random initialization baseline (verified by paired t-test, p < 0.05) within the 6-hour runtime limit.
2. **Given** the memory limit of 7GB RAM, **When** the training loop processes a batch, **Then** the process does not crash due to Out-Of-Memory (OOM) errors, utilizing only CPU resources.
3. **Given** a held-out validation set, **When** the training epoch completes, **Then** the validation loss does not exceed the training loss by more than a factor of 2, indicating no severe overfitting on the small sample.
4. **Given** the trained DistilledModel, **When** an ablation study is run, **Then** the system demonstrates that the predicted latents contain information independent of the text-only encoder (e.g., by showing that concatenating the predicted latents to the text embeddings yields a performance gain over the text-only baseline that cannot be explained by text redundancy alone).

---

### User Story 3 - Downstream Reasoning Evaluation (Priority: P3)

The system must evaluate the "augmented" model (text embeddings + predicted visual latents) against a standard text-only baseline on scientific reasoning tasks (e.g., table QA) using paired statistical testing.

**Why this priority**: This validates the ultimate value proposition: does the latent structure actually improve reasoning? This step determines if the research question is answered.

**Independent Test**: The evaluation script runs the trained model and the baseline on a fixed test set. The test verifies that the system outputs accuracy/F1 scores for both and performs a paired t-test to determine statistical significance.

**Acceptance Scenarios**:

1. **Given** a test set of scientific reasoning questions, **When** the augmented model and text-only baseline are evaluated, **Then** the system outputs performance metrics (Accuracy/F1) for both models.
2. **Given** the performance metrics from multiple random seeds, **When** the statistical analysis runs, **Then** a paired t-test is performed, and the p-value is reported; the system is considered successful if p < 0.05, confirming statistical significance.
3. **Given** a scenario where the augmented model performs worse than the baseline, **When** the analysis runs, **Then** the system still reports the delta and p-value, confirming the null result is statistically valid.
4. **Given** the final evaluation report, **When** the text is reviewed, **Then** it explicitly frames any performance improvements as ASSOCIATIONAL findings, avoiding causal claims about text "causing" layout understanding.
5. **Given** the augmented model and baseline, **When** the evaluation runs, **Then** the text-only baseline is re-trained for every random seed used in the augmented model to control for initialization variance, ensuring the paired t-test is statistically sound.

---

### Edge Cases

- **What happens when the text conversion loses critical layout information?** (e.g., a complex table is flattened into a linear string). The system must handle this by either skipping the sample or flagging it as a "low-information" case, ensuring the distillation target (visual latent) does not force the model to hallucinate structure that isn't in the text.
- **How does the system handle a frozen visual encoder that requires CUDA for loading?** The system must strictly enforce CPU-only inference; if the encoder cannot be loaded on CPU (even in inference mode), the pipeline must fail gracefully with a clear error message indicating the hardware incompatibility.
- **What if the dataset size exceeds the 7GB RAM limit during batch processing?** The system must implement a chunked processing strategy or reduce the batch size dynamically to ensure the entire pipeline remains within the 7GB memory constraint.

## Requirements

### Functional Requirements

- **FR-001**: System MUST ingest the scientific document corpus and generate visual layout latents using a frozen visual encoder for every document WITH valid layout annotations. (See US-1)
- **FR-002**: System MUST train a DistilledModel (50M parameters) to predict the visual layout latents from plain text input using MSE loss, ensuring the process completes within 6 hours on a CPU-only environment. (See US-2)
- **FR-003**: System MUST ensure the training process does not exceed 7GB of RAM usage, employing batch sizing or data chunking if necessary. (See US-2)
- **FR-004**: System MUST construct an "augmented" representation by concatenating the text embeddings with the predicted visual latents for downstream evaluation. (See US-3)
- **FR-005**: System MUST evaluate the augmented model and a text-only baseline on held-out scientific reasoning tasks and perform a paired t-test to assess statistical significance. (See US-3)
- **FR-006**: System MUST explicitly frame any performance improvements as ASSOCIATIONAL findings, avoiding causal claims about text "causing" layout understanding unless randomization is specified in the design. (See US-3)
- **FR-007**: System MUST fail gracefully with a clear error message if the combined dataset (primary + fallback sources) contains fewer than 10,000 pages with valid layout annotations. (See US-1)
- **FR-008**: System MUST perform an ablation study to demonstrate that the predicted visual latents contain information independent of the text-only encoder before downstream evaluation. (See US-2)
- **FR-009**: System MUST re-train the text-only baseline for every random seed used in the augmented model to ensure the paired t-test controls for initialization variance. (See US-3)

### Key Entities

- **DocumentPair**: Represents a single entry in the corpus containing `plain_text` (string) and `layout_annotations` (bounding boxes/structure), used to generate the target latent.
- **VisualLatent**: A fixed-dimension vector representing the structural layout information derived from the frozen visual encoder.
- **DistilledModel**: The lightweight Transformer (50M parameters) trained to map `plain_text` to `VisualLatent`.
- **ReasoningTask**: A specific downstream task (e.g., Table QA) used to evaluate the augmented representation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The MSE loss of the distilled model on the validation set is measured against the random initialization baseline to confirm learning. (See FR-002)
- **SC-002**: The accuracy/F1 score of the augmented model is measured against the text-only baseline on the held-out test set to quantify performance delta. (See FR-005)
- **SC-003**: The statistical significance (p-value) of the performance delta is measured against the standard threshold of 0.05; success is defined as p < 0.05. (See FR-006)
- **SC-004**: The peak memory usage during training is measured against the 7GB limit to ensure CPU-tractability. (See FR-003)
- **SC-005**: The total runtime of the distillation and evaluation pipeline is measured against the 6-hour limit to ensure feasibility on free-tier CI. (See FR-002)
- **SC-006**: The total count of documents with valid layout annotations (primary + fallback) is measured against the [deferred]-page minimum to ensure data sufficiency. (See FR-007)
- **SC-007**: The ratio of validation loss to training loss is measured against the threshold of 2.0 to detect overfitting. (See US-2)

## Assumptions

- The public weights for the frozen visual encoder can be loaded and executed in inference mode on a CPU-only environment (e.g., using `torch.no_grad()` and default precision) without requiring CUDA or specific GPU drivers.
- The scientific document corpus (e.g., from llmXive or HuggingFace) contains paired plain text and ground-truth layout annotations for at least 10,000 pages, and the text conversion process preserves sufficient syntactic cues for the model to learn the mapping.
- The "visual layout latents" generated by the frozen encoder are a valid proxy for the "structural information" required for downstream reasoning tasks, even if the text input lacks explicit visual tokens.
- The 50M parameter Transformer model size is sufficient to approximate the visual latents within the 6-hour runtime and 7GB RAM constraints; larger models are out of scope.
- The downstream reasoning tasks (Table QA, equation parsing) are available as a held-out test set with ground-truth labels, and the dataset size is small enough to fit in memory for evaluation.
- The dataset variables (text content, layout annotations) are sufficient for the proposed analysis; no additional external data sources are required. The system utilizes the `llmXive-layout-distillation` subset of the corpus, which is explicitly defined to contain paired `plain_text` and `layout_annotations` (bounding boxes and structure) for ≥10,000 pages. If the primary source lacks specific bounding box granularity for a page, the system falls back to the `layout-parser` derived annotations from the same source; if neither is present, the page is skipped. No external data source is required unless the primary subset falls below the [deferred]-page minimum, in which case the `pubmed-layout` subset is appended to meet the volume requirement. If the combined total of valid pages remains below [deferred] after all fallbacks, the system terminates with a failure state as defined in FR-007.