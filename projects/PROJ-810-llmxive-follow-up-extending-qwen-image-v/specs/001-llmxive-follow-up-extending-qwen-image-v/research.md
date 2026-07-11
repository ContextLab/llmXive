# Research: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Research Objective

To empirically validate the hypothesis that the Qwen-Image-VAE-2.0 latent space geometrically separates textual and visual features, enabling linear vector arithmetic for zero-shot semantic editing. This research addresses the core scientific inquiry (US-01), demonstrates practical utility (US-02), and ensures methodological soundness (US-03).

## Dataset Strategy

### Primary Dataset: OmniDoc-1

The project relies on the **OmniDoc-1** dataset, which contains document images with ground-truth bounding boxes for text and image regions. This dataset serves as the proxy for the "OmniDoc-TokenBench" referenced in the spec, as the latter has no verified source.

- **Source**: HuggingFace Hub (Verified)
- **URL**: `https://huggingface.co/datasets/omnineura/Omni-Doc-1/resolve/main/data/train-00000-of-00001.parquet`
- **Access Method**: `datasets.load_dataset("parquet", data_files=URL)`
- **Relevance**: Contains the necessary `image` column and `bbox` annotations.
- **Variable Fit Check**:
  - *Required*: Image data, Bounding box coordinates, Modality labels (text/image).
  - *Available*: The parquet file contains image bytes and metadata.
  - *Constraint*: The dataset does not contain "post-task anxiety" or other psychological variables; this is a computer vision task, so the fit is correct.

### Data Loading Strategy & Label Integrity (Circularity Break)

1.  **Download**: Fetch the Parquet file from the verified URL.
2.  **Checksum**: Compute SHA-256 hash and record in `state/...yaml`.
3.  **Parse**: Load into a Pandas DataFrame.
4.  **Filter (Critical)**: Extract rows where `region_type` (or equivalent metadata field) is explicitly "text" or "image".
    - **Exclusion Rule**: Rows where the modality label is missing, ambiguous, or "mixed" are **excluded** from the separability analysis (US-01) to prevent circularity.
    - **Fallback**: If explicit labels are missing for a region, that region is excluded from the *training* of the SVM. It may be used for *evaluation* only if an independent, non-OCR heuristic (e.g., spatial position) can be proven to be unbiased, but the default is exclusion.
5.  **Gold Standard Annotation (Methodology Fix)**:
    - **Action**: Randomly select a stratified subset (e.g., 500 samples) of the filtered dataset.
    - **Process**: A human annotator verifies if the `region_type` label matches the visual content (text vs. image).
    - **Result**: This creates a **Gold Standard** label set.
    - **Usage**: The SVM (US-01) is trained *only* on this Gold Standard subset. This breaks the tautology where the 'ground truth' is the same source as the crop selection.
6.  **Crop**: Use bounding box coordinates to crop the image into text-only and image-only regions.
7.  **Sample**: If the dataset exceeds memory limits, sample a stratified subset to ensure CPU feasibility while maintaining statistical power.

### Independent Ground-Truth Validation (Methodology Fix)

To address the concern of circularity (where crop selection heuristics might match evaluation labels):
1.  **Manual Spot-Check**: See 'Gold Standard Annotation' above. If >5% discrepancy is found in the Gold Standard, the dataset's label reliability is flagged, and the SVM training set is reduced.
2.  **Cross-Validation**: Run a secondary OCR engine (Tesseract) on the crops *only* to filter out 'mixed' regions. If the dataset labels "text" but Tesseract finds no text, or vice versa, the sample is marked as "ambiguous" and excluded. This ensures the ground truth is not solely dependent on the dataset's metadata.

## Model Strategy

### VAE Encoder/Decoder

- **Primary Source**: HuggingFace Model Hub (Identifier: `Qwen/Qwen-Image-VAE-2.0`).
- **Fallback Strategy**: If `Qwen/Qwen-Image-VAE-2.0` is unavailable or un-loadable on CPU (e.g., missing CPU wheels, CUDA dependencies), the plan will substitute with **DINOv2 (vit_base_patch14)** for feature extraction. This is documented as a "Fallback-Model" in the output schema.
- **Loading**: Load in `float32` precision (no 8-bit/4-bit quantization) to avoid CUDA dependencies. Use `torch.no_grad()` for inference.
- **Device**: `cpu` only.
- **Memory Management**: Process images in small batches (e.g., 16-32) to stay within 7 GB RAM.

### Classifier (US-01)

- **Model**: Linear SVM (`sklearn.svm.LinearSVC`) or Logistic Regression (`sklearn.linear_model.LogisticRegression`).
- **Rationale**: Lightweight, CPU-tractable, and sufficient for testing linear separability.
- **Input**: Flattened latent vectors (or PCA-reduced if dimensionality is too high for SVM).

### OCR Engine (US-02)

- **Model**: PaddleOCR (CPU-only mode).
- **Rationale**: Robust text recognition for verifying edited content.
- **Metric Link**: OCR results are stored in `data/metrics/ocr_results.json` and validated against `contracts/output_metrics.schema.yaml`.

## Methodology & Statistical Rigor

### Phase 1: Latent Space Disentanglement (US-01)

1.  **Triviality Check**:
    - Run a classifier on raw pixel statistics (e.g., mean intensity, simple color histograms) of the crops.
    - **Goal**: Determine if >99% separability is achievable without the VAE.
    - **Output**: If true, set `triviality_flag` = true in `output.schema.yaml` and flag the latent analysis as potentially trivial.
2.  **Encoding**: Encode all valid text-only and image-only crops into latent vectors $z$.
3.  **Spatial Randomization Control**:
    - Generate control vectors by taking text crops and randomly shuffling their spatial coordinates (or rotating them) to break semantic content while preserving texture.
    - Train a classifier on these randomized vectors.
    - **Goal**: If accuracy remains high, the VAE is encoding spatial layout, not semantic modality. This result is reported as a confounding factor.
4.  **Classifier Training**:
    - Split **Gold Standard** data into train/test (e.g., 80/20) stratified by modality.
    - Train Linear SVM on train set.
    - Evaluate on test set: Accuracy, F1-score.
 - **Hypothesis**: Accuracy $\ge$ [deferred], F1 $\ge$ 0.90.
5.  **Cross-Document Direction Consistency (Primary Validation)**:
    - Compute centroids $\mu_{text}$ and $\mu_{image}$ for *each* document in the dataset.
    - Check if the difference vector direction ($\mu_{text} - \mu_{image}$) is consistent across different documents (e.g., cosine similarity > 0.9).
    - **Output**: Set `linearity_verified` = true only if direction consistency is high and PCA 2D projection shows clear separation. This tests if the geometric structure is a property of the VAE, not just the dataset.
6.  **Permutation Test**:
    - Shuffle labels multiple times.
    - Retrain classifier on shuffled data.
    - Compute p-value: $P(\text{Acc}_{shuffled} \ge \text{Acc}_{observed})$.
    - **Criterion**: $p < 0.05$.
7.  **Power Analysis**:
    - **Pre-study Justification**: Sample size (N=10k) is justified by a hypothesized large effect size (Cohen's d > 0.8) based on literature/assumptions.
    - **Reporting**: If the *achieved* power (calculated from observed effect) is < 0.8, report "inconclusive" with specific power value as a limitation. Do not use this to validate the sample size.

### Phase 2: Zero-Shot Semantic Editing (US-02)

1.  **Centroid Computation**:
    - Compute $\mu_{text}$ (mean of text latent vectors) and $\mu_{image}$ (mean of image latent vectors).
2.  **Global Mean Control**:
    - Compute the global dataset mean $\mu_{global}$.
    - Perform vector arithmetic using $\mu_{global}$ instead of $\mu_{text}$.
    - **Goal**: Ensure the editing effect is not just shifting the vector towards a generic mean.
3.  **Unrelated Document Control**:
    - Compute centroids from a completely different dataset or a different modality subset (e.g., only "mixed" regions).
    - Perform the same vector arithmetic.
    - **Goal**: Ensure the editing effect is specific to the text/image semantic relationship.
4.  **Vector Arithmetic**:
    - For a source document $z_{doc}$, compute $z_{new} = z_{doc} - \mu_{text\_old} + \mu_{text\_new}$.
5.  **Decoding**: Decode $z_{new}$ to image.
6.  **Evaluation**:
    - **Reconstruction Baseline**: Re-encode and decode the original image *without* arithmetic.
    - **Masked SSIM**: Compare non-text regions of original and edited image. Compare this score against the Baseline SSIM.
 - **OCR Accuracy**: Run PaddleOCR on edited image; compare recognized text to target. Target $\ge$ [deferred] character accuracy.
    - **Runtime**: Measure execution time; target $\le$ 60s/image.
    - **Layout Preservation Control**:
        - Generate edge maps of the *original* and *edited* images using Canny edge detection (independent of VAE).
        - Compute SSIM between these edge maps.
        - **Goal**: If Masked SSIM fails but Edge SSIM is high, the failure is due to texture/artifacts, not layout distortion. If Edge SSIM is low, the layout was distorted.

### Phase 3: Statistical Validation (US-03)

1.  **Sensitivity Analysis**:
    - Sweep classification threshold (for SVM probability) over a range (e.g., 0.1 to 0.9).
    - Plot False Positive Rate (FPR) vs. False Negative Rate (FNR).
    - **Goal**: Confirm robustness of the decision boundary (dependent on optimal boundary from T018).
2.  **Multiple Comparisons**:
    - Perform individual significance tests for Accuracy, F1, SSIM.
    - **Correction**: Do NOT apply Bonferroni across different metric types (as per spec SC-009). Apply corrections only if multiple tests are run on the *same* metric (e.g., different thresholds).
3.  **Collinearity Check**:
    - Verify that text and image regions are not definitionally overlapping (e.g., text inside an image). Exclude ambiguous regions.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **OmniDoc-1 lacks explicit modality labels** | High (US-01 fails) | Exclude rows with missing/ambiguous labels from training. Do not infer labels via OCR heuristics for the SVM ground truth. Use **Gold Standard** manual annotation for training. |
| **Dataset too large for 7 GB RAM** | High (Runtime failure) | Sample stratified subset (e.g., 10k rows) before processing. Use chunked processing for encoding. |
| **VAE model unavailable** | High (US-01/US-02 fail) | Use DINOv2 (vit_base_patch14) as fallback. Document as "Fallback-Model" in output. |
| **Vector arithmetic fails to preserve layout** | Medium (US-02 fails) | Compare against Reconstruction Baseline. Report low SSIM and flag as "artifacts present". Use Layout Preservation Control. |
| **OCR fails on edited text** | Medium (US-02 fails) | Use multiple OCR engines or report "OCR failure" as a metric. |

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use OmniDoc-1 instead of TokenBench** | TokenBench has no verified source; OmniDoc-1 is the only verified dataset with document images and bounding boxes. |
| **CPU-only inference for VAE** | Constraint of 2 vCPU/7 GB RAM; GPU dependencies would cause CI failure. |
| **Linear SVM for separability** | Lightweight, interpretable, and sufficient for testing linear separability hypothesis. |
| **No Bonferroni across metric types** | Per spec SC-009, distinct metrics (Accuracy, SSIM) are tested individually. |
| **Pre-study Power Analysis** | Post-hoc power analysis is invalid for sample size justification. Sample size justified by hypothesized effect size. |
| **Fallback Model Strategy** | DINOv2 used if Qwen-Image-VAE-2.0 is unavailable to ensure compute feasibility. |
| **Independent Ground-Truth Validation** | Required to break circularity between crop selection and evaluation labels. |
| **Layout Preservation Control** | Required to distinguish between disentanglement failure and VAE reconstruction artifacts. |
| **Null Hypothesis Control** | Required to prove vector arithmetic performs semantic editing, not just shifting to a generic mean. |
| **Gold Standard Annotation** | Required to obtain ground truth labels independent of the dataset's metadata. |
| **Cross-Document Direction Consistency** | Required to validate that the geometric structure is a property of the VAE, not just the dataset. |
| **Global Mean / Unrelated Document Controls** | Required to prove vector arithmetic is semantic editing, not just generic vector shifting. |