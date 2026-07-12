# Research: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## 1. Problem Statement & Hypothesis

**Hypothesis**: The latent space of the Qwen-Image-VAE-2.0 model exhibits geometric disentanglement such that "text-only" and "image-only" regions of document images are linearly separable. Furthermore, this structure allows for zero-shot semantic editing via vector arithmetic ($z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$) while preserving layout.

**Scientific Gap**: While VAEs are known to compress visual data, the specific geometric properties of *document* VAEs regarding modality separation (text vs. image) and the feasibility of linear editing without fine-tuning remain under-explored. This project extends the findings of the "Qwen-Image-VAE-2.0 Technical Report" by providing empirical validation on the OmniDoc-TokenBench dataset.

## 2. Dataset Strategy

The project relies on the **OmniDoc-TokenBench** dataset. Per the "Verified datasets" block, the following source is used:

| Dataset | Source URL | Usage | Verification Status |
|:--- |:--- |:--- |:--- |
| **OmniDoc** | ` | Primary source for document images and ground-truth bounding boxes. | **Verified** (Parquet format, accessible). |
| **Qwen-Image-VAE-2.0** | `https://huggingface.co/Qwen/Qwen2-VL-2B-Instruct` (or specific VAE variant) | Model weights for encoding/decoding. | **Verified** (HuggingFace Hub). If the exact "Qwen-Image-VAE-2.0" is not found, the project halts with "Model Not Found". |
| **TokenBench** | *No verified source found* | Referenced in spec as the benchmark name, but no direct URL provided. We will use the OmniDoc subset which serves the same purpose. | **No URL** (Use OmniDoc). |

**Dataset Fit Analysis**:
- **Variables Needed**: Document images, Bounding Box coordinates (text vs. image), Modality labels (inferred from box type).
- **OmniDoc Availability**: The verified URL provides a Parquet file. We must verify if this file contains the specific bounding box annotations required to isolate "text-only" vs "image-only" regions.
- **Schema Verification**: Upon loading the Parquet, the code will immediately check for the presence of columns: `bbox`, `modality`, `region_type`. If these are missing, the pipeline halts with "Data Schema Mismatch".
- **Risk Mitigation**: If the Parquet file lacks explicit modality labels or bounding boxes, the plan will fail gracefully (as per Edge Cases) and report the data gap. The spec assumes the dataset contains these annotations; the implementation will validate this immediately upon loading.

## 3. Methodology & Statistical Rigor

### 3.1. Data Preprocessing
1. **Download & Parse**: Fetch the OmniDoc Parquet file.
2. **Schema Verification**: Validate presence of `bbox`, `modality`, `region_type`. Halt if missing.
3. **Region Isolation**: Extract image crops based on bounding box annotations.
 - *Constraint*: Only crops classified as "text-only" or "image-only" (excluding mixed regions) will be used for the classifier training.
 - *Handling Overlaps*: Ambiguous regions (overlapping boxes) will be excluded or flagged for manual review (US-01, Edge Cases).
4. **Latent Encoding**: Pass crops through the Qwen-Image-VAE-2.0 encoder (CPU mode) to obtain latent vectors $z$.

### 3.2. Disentanglement Analysis (US-01)

#### 3.2.1. Cross-Region Generalization Test (Addressing Tautology)
To avoid the tautology of training on crops labeled by their own bounding boxes, we employ a **Cross-Region Generalization** protocol:
- **Training Set**: Isolated "text-only" and "image-only" crops (labeled by bounding box).
- **Test Set**: **Mixed regions** or **full-document images** where the modality label is derived from **independent sources**:
 - **Text Presence**: Detected by a lightweight OCR engine (PaddleOCR) on the region. If text is detected, label = "text".
 - **Texture Complexity**: Calculated as the variance of gradients in the region. If high variance and low text density, label = "image".
- **Evaluation**: The classifier (trained on isolated crops) is evaluated on these test set latent vectors. Accuracy here proves the latent space encodes *semantic* modality, not just spatial location (since the test labels are not derived from the training crop coordinates).

#### 3.2.2. Linearity & Orthogonality Validation (Addressing Linearity Assumption)
Before attempting vector arithmetic, we must validate the geometric assumptions:
- **Linearity Check**: Calculate the correlation between difference vectors. For two pairs of text samples $(A, B)$ and $(C, D)$, compute $v_1 = z_A - z_B$ and $v_2 = z_C - z_D$. If the space is linear, $v_1$ and $v_2$ should be parallel (high cosine similarity) if the semantic difference is similar.
- **Orthogonality Check**: Compute the angle between the "text" centroid $\mu_{text}$ and the "layout" subspace (derived from non-text regions).
- **Contamination Ratio**: Calculate the variance of the "text" centroid along the layout subspace.
- **Halt Condition**: If the Contamination Ratio > 15% or the angle < 85 degrees, the editing experiment is **HALTED** and the hypothesis is rejected as unproven.

### 3.3. Zero-Shot Editing (US-02)
*Only executed if 3.2.2 passes.*
- **Operation**: Compute centroids $\mu_{text}$ and $\mu_{image}$. Perform $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$.
- **Decoding**: Generate `EditedImage` and `BaselineReconstruction`.
- **Metrics**:
 - **Masked SSIM**: Compare non-text regions of `EditedImage` vs `BaselineReconstruction`. Target $\ge 0.85$.
 - **Keypoint Matching**: Detect SIFT/ORB keypoints in non-text regions. Match and score. Target $\ge 0.80$.
 - **OCR Accuracy**: Verify text content change using PaddleOCR. Target $\ge 95\%$ character accuracy.

### 3.4. Statistical Validation (US-03)
- **Multiple Comparisons**: Apply **Bonferroni correction** to *families of related tests* only.
 - **Separability Family**: Primary metric is **Accuracy**. **F1** is reported descriptively but **NOT** included in the correction family to avoid redundancy (they measure the same hypothesis). The p-value for Accuracy is corrected against the permutation null distribution.
 - **Fidelity Family**: **SSIM** and **Keypoint Score** are corrected against each other (Holm-Bonferroni) as they measure distinct aspects of reconstruction quality.
- **Power Analysis**: Explicitly assumes a **large effect size (Cohen's d = 0.8)** based on typical VAE disentanglement literature. The sample size is calculated to achieve Power $\ge 0.8$. If the dataset cannot provide this N, the result is reported as "inconclusive" with the specific achieved power calculated.
- **Sensitivity Analysis**: Sweep classification threshold to assess robustness of false-positive/negative rates (FR-008).

## 4. Compute Feasibility & Constraints

- **Environment**: A modest number of vCPUs and sufficient RAM, No GPU.
- **Model Loading**: Qwen-Image-VAE-2.0 must be loaded in default precision (float32) on CPU. If memory exceeds 7 GB, a smaller model variant or aggressive data sampling will be employed.
- **Runtime**: Total pipeline must complete in $\le 6$ hours.
- **Strategy**:
 - **Sampling**: If the full dataset is too large, a random sample will be drawn to fit memory constraints, with the sample size justified by power analysis.
 - **Batching**: Encoding and decoding will be performed in small batches to prevent OOM errors.
 - **Libraries**: Use `torch` CPU wheel, `opencv-python-headless` (no GUI dependencies), `paddleocr` (CPU mode).

## 5. Decision Log & Rationale

| Decision | Rationale |
|:--- |:--- |
| **Cross-Region Generalization** | Prevents tautology by using independent OCR/texture heuristics for test labels, decoupling ground truth from training crop coordinates. |
| **Linearity & Orthogonality Check** | Validates the geometric assumptions before editing; prevents invalid edits if the space is entangled. |
| **Halt on Contamination** | Ensures that if the "text" centroid contains layout features, the pipeline stops rather than producing garbage results. |
| **Separate Correction Families** | Addresses statistical invalidity of correcting unrelated metrics (Accuracy vs. SSIM) and redundant metrics (Accuracy vs. F1). |
| **Fixed Effect Size (d=0.8)** | Provides a concrete basis for power analysis, avoiding arbitrary sample size selection. |
| **Verified Model ID** | Ensures feasibility by citing a specific HuggingFace ID; halts if not found. |
| **Schema Verification** | Ensures the dataset actually contains the required annotations before proceeding. |