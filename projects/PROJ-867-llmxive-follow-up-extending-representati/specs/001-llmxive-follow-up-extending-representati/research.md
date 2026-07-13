# Research: llmXive follow-up: extending Representation Forcing for Structured Text Generation

## 1. Research Question & Hypothesis

**Primary Research Question**: Can intermediate representation tokens from a frozen Representation Forcing (RF) encoder enable a lightweight autoregressive model (~30M params) to reconstruct structured text (JSON/Markdown) from document images with higher syntactic validity and structural fidelity than a pixel-based baseline, under strict CPU resource constraints?

**Hypothesis**: The RF-based model will achieve a statistically significant (p < 0.05) higher syntactic validity rate and lower AST edit distance compared to a pixel-based baseline on a per-image basis, demonstrating that RF tokens capture structural priors independent of raw pixel features. Results will be framed as "performance under extreme resource constraints" rather than optimal performance.

## 2. Dataset Strategy

### Verified Datasets
The following datasets are used, sourced exclusively from the verified list provided in the project context:

| Dataset | Purpose | Source URL | Notes |
|:--- |:--- |:--- |:--- |
| **PubLayNet** | Primary dataset for document images and layout annotations. | ` (Train), ` (Test) | Contains bounding boxes and text content. Used to generate JSON/Markdown ground truth. CodeParrot is excluded due to lack of document-image alignment. |
| **LayoutLMv3** | Frozen RF Encoder (Proxy). | `https://huggingface.co/microsoft/layoutlmv3-base` | Verified HuggingFace model. Used as the frozen RF encoder to extract structural tokens. |

**Dataset-Variables Fit**:
- **PubLayNet**: Contains `boxes` (layout) and `text` (content). These map directly to the "structural priors" needed for JSON/Markdown generation.
- **Ground Truth Construction**: PubLayNet annotations (boxes + text) will be programmatically converted to a canonical JSON schema (e.g., `{"layout": [{"box": [...], "text": "..."}]}`). This ensures "syntactic validity" is a measure of reconstruction accuracy against a deterministic, schema-compliant target, avoiding tautology by verifying the generated JSON matches the *content* of the ground truth, not just the syntax.
- **Constraint**: If the full PubLayNet dataset exceeds RAM, a random subset (e.g., a large collection of images) will be used, ensuring stratification by layout complexity (single vs. multi-column).

## 3. Model Architecture & Strategy

### 3.1 RF Encoder (Frozen)
- **Source**: `microsoft/layoutlmv3-base` (frozen weights).
- **Operation**: Frozen weights. Input: Document image. Output: Sequence of intermediate tokens (vectors).
- **Constraint**: No pixel-decoding layers are instantiated. Only the encoder forward pass is executed.

### 3.2 Lightweight Autoregressive Model (RF Model)
- **Architecture**: Small Transformer (GPT-style) with ~30M parameters (reduced from a large-scale baseline for CPU feasibility).
- **Input**: RF token sequences (padded/truncated to fixed context window of 512 tokens).
- **Output**: Tokenized structured text (JSON/Markdown).
- **Training**: Max epochs (Constitution VII) or until validation loss plateaus (Spec FR-003). **Constitution VII takes precedence** (2 epochs) to ensure CPU tractability. A sensitivity analysis with a varying number of epochs will be attempted if RAM permits.
- **Optimizer**: AdamW with default learning rate.
- **Batch Size**: Dynamically adjusted to fit 4GB RAM (e.g., 4-8).

### 3.3 Pixel-Baseline Model
- **Architecture**: Simple CNN encoder (e.g., ResNet-18 or custom lightweight CNN) + Lightweight Transformer decoder.
- **Input**: Downsampled raw image pixels (e.g., 224x224).
- **Output**: Tokenized structured text.
- **Training**: Same constraints as RF Model (limited epochs, same optimizer).

## 4. Evaluation Metrics & Statistical Analysis

### 4.1 Metrics
1. **Syntactic Validity**: Binary (0/1) based on parser acceptance (JSON/Markdown) and content matching against the canonical ground truth.
2. **AST Edit Distance**: Quantitative measure of structural fidelity between generated and ground truth ASTs. This is the primary metric for "structural independence."
3. **Complexity Overflow Rate**: Percentage of samples where token sequence exceeds the fixed context window (512), requiring truncation.
4. **Total Runtime**: Total training and evaluation time in seconds.

### 4.2 Statistical Testing
- **Unit of Analysis**: Document Image (N > 10k), not random seeds.
- **Test for Validity**: McNemar's test for paired binary outcomes (validity per image) to compare RF vs. Baseline models.
- **Test for AST Distance**: Wilcoxon signed-rank test on per-image AST edit distances.
- **Significance Threshold**: p < 0.05.
- **Power Analysis**: Given the large N, power is sufficient. to detect small effect sizes.

## 5. Decision Rationale & Feasibility

- **Why 2 Epochs?**: Constitution VII mandates a maximum of 2 epochs to ensure CPU tractability. This is a conservative headroom below the Spec's epoch limit. The hypothesis is that even with limited training, the RF tokens should yield a significant performance gap if they truly contain structural priors. Results will be explicitly framed as "under extreme resource constraints."
- **Why ~30M Params?**: A 100M model on CPU is computationally infeasible within 6 hours. 30M is a conservative approximation that maintains the "lightweight" hypothesis while guaranteeing runtime feasibility.
- **Why No CodeParrot?**: CodeParrot lacks document-image alignment. The study focuses exclusively on PubLayNet for layout-to-structure tasks.
- **Memory Management**: Data will be processed in batches. Intermediate tensors will be deleted immediately after use. `resource_monitor.py` will enforce a hard kill-switch at a predefined memory threshold

The research question remains: [Research Question]
The method remains: [Method]
References: [References].

## 6. Ethical & Reproducibility Considerations

- **Reproducibility**: All random seeds are pinned. Code and data paths are absolute relative to the project root.
- **Bias**: The study uses public datasets (PubLayNet). No PII is expected, but a PII scan is run on the data pipeline.
- **Causal Claims**: The study is observational (comparing two training approaches). Claims are framed as "associational improvements" rather than causal guarantees of "structural understanding."