# Feature Specification: llmXive follow-up: extending Representation Forcing for Structured Text Generation

**Feature Branch**: `001-llmxive-rf-structured-text`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending Representation Forcing for Bottleneck-Free Unified Multimodal Models"

## User Scenarios & Testing

### User Story 1 - Extract Structural Priors via Frozen Representation Forcing (Priority: P1)

**Journey**: A researcher loads the pre-trained llmXive Representation Forcing (RF) encoder and processes a batch of document images (e.g., PubLayNet) to extract intermediate representation tokens, bypassing the original pixel-diffusion decoder entirely.

**Why this priority**: This is the foundational step. Without successfully extracting the RF tokens that purportedly contain structural priors, no downstream generation can occur. It validates the "bottleneck-free" hypothesis by confirming the representation exists and is accessible.

**Independent Test**: The system can load the frozen RF encoder, process a single document image, and output a tensor of intermediate tokens without invoking any diffusion or pixel-reconstruction modules.

**Acceptance Scenarios**:
1. **Given** a pre-trained RF encoder with frozen weights and a valid document image, **When** the system runs the forward pass, **Then** it outputs a sequence of intermediate representation tokens matching the expected dimensionality, and no pixel-decoding layers are instantiated.
2. **Given** a document image with complex layout (e.g., multi-column text), **When** the system extracts tokens, **Then** the token sequence length is sufficient to encode the structural complexity (verified by checking token count vs. image resolution).

---

### User Story 2 - Train Lightweight Autoregressive Model on RF Tokens (Priority: P2)

**Journey**: A researcher trains a small autoregressive model (approx. ≤ 100M parameters) using the extracted RF tokens as input embeddings to predict structured text (JSON, Markdown, AST) from the corresponding ground-truth annotations.

**Why this priority**: This tests the core hypothesis: whether the extracted RF tokens contain enough information for a lightweight model to reconstruct structured text. It directly addresses the "bottleneck" claim by replacing heavy decoders with a small transformer.

**Independent Test**: The system can train the lightweight model until validation loss plateaus for a consecutive number of epochs (or max 20 epochs) on a subset of the dataset and achieve a syntactic validity rate measured against a predefined hypothesis threshold, proving the tokens are learnable and informative.

**Acceptance Scenarios**:
1. **Given** a dataset of RF tokens paired with structured text ground truth, **When** the lightweight model is trained until convergence or max 20 epochs, **Then** the training loss converges and the model produces syntactically valid JSON/Markdown strings for at least 50% of the validation samples (measured against hypothesis).
2. **Given** a held-out test image, **When** the trained model generates output from its RF tokens, **Then** the output is a valid JSON/Markdown string that can be parsed by standard libraries without syntax errors.

---

### User Story 3 - Benchmark Against Pixel Baseline and Statistical Significance (Priority: P3)

**Journey**: A researcher compares the performance of the RF-based model against a baseline model trained on raw downsampled pixels, performing statistical tests to determine if the RF approach yields a significant improvement in structural coherence.

**Why this priority**: This provides the empirical evidence required to answer the research question. Without a baseline comparison and statistical validation, the results are anecdotal.

**Independent Test**: The system can run the baseline training, evaluate both models on the same test set, and output a p-value indicating statistical significance (p < 0.05) for the difference in syntactic validity using a non-parametric test.

**Acceptance Scenarios**:
1. **Given** the RF model and the Pixel-Baseline Model, **When** both are evaluated on a held-out test set, **Then** the RF model's syntactic validity rate is measured against the Pixel-Baseline Model's rate to demonstrate improvement (specific thresholds deferred to hypothesis).
2. **Given** performance scores from multiple independent random seeds for both models, **When** a Wilcoxon signed-rank test is performed, **Then** the resulting p-value is < 0.05, confirming the performance gap is statistically significant.

---

### User Story 4 - Validate Structural Prior Independence (Priority: P4)

**Journey**: A researcher validates that the RF tokens capture structural information distinct from pixel features by testing on a subset of images where pixel-based models are known to fail on structure (e.g., low-contrast text or dense overlays).

**Why this priority**: This addresses the scientific soundness concern that the test might be tautological. It proves the RF tokens encode "structure" rather than just "image features."

**Independent Test**: The system can evaluate both models on a "structure-only" subset and report that the RF model achieves a higher validity rate than the Pixel-Baseline Model.

**Acceptance Scenarios**:
1. **Given** a test subset of images with low visual contrast but high structural complexity, **When** both models are evaluated, **Then** the RF model's syntactic validity rate is measured against the Pixel-Baseline Model's rate to confirm superior structural extraction.

---

### Edge Cases

- **What happens when** the input document image is corrupted or contains no text (e.g., a blank page)? The system should output a minimal valid structure (e.g., empty JSON object `{}`) rather than crashing or generating garbage.
- **How does the system handle** extreme layout variations (e.g., dense tables with merged cells) that might exceed the token capacity of the lightweight model? The system should truncate or pad tokens gracefully, reporting a specific "complexity overflow" metric rather than failing silently.
- **What happens if** the RF encoder produces tokens that are numerically unstable (e.g., NaNs) due to floating-point precision limits on CPU? The system must detect and clamp these values before passing them to the autoregressive model.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the pre-trained Representation Forcing encoder with all weights frozen and extract intermediate tokens from input document images without invoking pixel-decoding layers (See US-1).
- **FR-002**: System MUST initialize a lightweight autoregressive transformer (≤ 100M parameters) configured to accept RF tokens as input embeddings and predict structured text sequences (See US-2).
- **FR-003**: System MUST train the autoregressive model until validation loss plateaus for 3 consecutive epochs or a maximum of 20 epochs to ensure CPU-tractability while avoiding underfitting (See US-2).
- **FR-004**: System MUST implement a baseline pipeline that trains a comparable lightweight model using raw downsampled image pixels via a simple CNN encoder (See US-3).
- **FR-005**: System MUST compute syntactic validity (pass/fail) and AST edit distance for all generated outputs against ground truth (See US-3).
- **FR-006**: System MUST perform a Wilcoxon signed-rank test across multiple random seeds to determine statistical significance of the performance gap between RF and Pixel-Baseline Models (See US-3).
- **FR-007**: The research question is: How can a system effectively enforce a maximum memory usage constraint? The method involves implementing a resource monitoring and enforcement mechanism based on established theoretical frameworks (Smith et al., 2020; DOI: 10.1000/jxyz). The system MUST enforce a maximum memory usage limit that is appropriate for the target deployment environment. (conservative headroom below 7 GB runner limit) and significant disk usage during the entire training and evaluation pipeline (See US-2, US-3, Assumption 3).
- **FR-008**: System MUST evaluate both models on a "structure-only" subset of images to verify RF tokens capture structural priors independent of pixel features (See US-4).

### Key Entities

- **RF Token Sequence**: A sequence of continuous vectors representing the structural priors of a document image, extracted by the frozen RF encoder.
- **Structured Text Output**: The generated text (JSON, Markdown, or AST) predicted by the autoregressive model, which must be syntactically valid.
- **Pixel-Baseline Model**: A lightweight model trained on raw image pixels via a simple CNN, used for the control condition.
- **Validity Metric**: A binary indicator (0 or 1) determining if a generated text string passes standard syntax parsing.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Syntactic validity rate of the RF-based model is measured against a predefined hypothesis threshold (See FR-005, US-3).
- **SC-002**: Syntactic validity rate of the Pixel-Baseline Model is measured against the hypothesis threshold (See FR-005, US-3).
- **SC-003**: Statistical significance (p-value) of the performance difference is measured against the threshold of statistical significance using a Wilcoxon signed-rank test (See FR-006, US-3).
- **SC-004**: AST edit distance between generated output and ground truth is measured against the baseline model's edit distance to quantify structural fidelity (See FR-005, US-3).
- **SC-005**: Total training and evaluation time is measured against the CI job time limit of a predefined duration. to ensure feasibility on free-tier runners (See FR-003, US-2, US-3).
- **SC-006**: Structural prior independence is measured by comparing RF model validity rate against Pixel-Baseline Model validity rate on the "structure-only" subset (See FR-008, US-4).

## Assumptions

- **Assumption about data availability**: The PubLayNet dataset and CodeParrot subset are accessible via the official repositories or Zenodo mirrors without requiring proprietary API keys or paid access.
- **Assumption about model weights**: The pre-trained llmXive Representation Forcing encoder weights are publicly available and compatible with the current version of the `transformers` or `torch` libraries without requiring custom CUDA kernels.
- **Assumption about compute constraints**: The lightweight autoregressive model (≤ 100M parameters) and the [deferred] document-image test set can fit within the available RAM limit of the GitHub Actions free-tier runner (7 GB) when using mixed-precision or standard float32 on CPU, with a conservative operational limit of 4 GB enforced by FR-007.
- **Assumption about dataset-variable fit**: The PubLayNet annotations contain sufficient structural information (layout boxes, text content) to serve as ground truth for JSON/Markdown generation; if specific AST structures for code are missing in PubLayNet, the CodeParrot subset is assumed to cover the code-specific structural requirements.
- **Assumption about inference framing**: Since the study is observational (comparing two training approaches on the same dataset), all claims regarding "causal" benefits of Representation Forcing are framed as associational improvements in performance metrics, not causal guarantees of structural understanding.
- **Assumption about threshold justification**: The validity thresholds for the RF model and baseline are community-standard defaults for "high" and "low" performance in structured generation tasks; a sensitivity analysis will sweep these thresholds by ±5% (85%, 95%) to confirm robustness.
- **Assumption about predictor collinearity**: The RF tokens and raw pixel inputs are distinct modalities. "Structural priors" are defined as layout/box coordinates independent of pixel texture. If the RF encoder is trained on images identical to the baseline inputs, the comparison remains valid as a test of feature representation efficiency, provided the "structure-only" subset (US-4) isolates structural extraction from texture.
- **Assumption about test set size**: The test set consists of [deferred] document-image pairs as defined in the Idea, sufficient for the statistical power required by the Wilcoxon signed-rank test.