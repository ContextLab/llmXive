# Research: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

## Overview

This research phase addresses the acquisition of data, the methodology for visual complexity extraction, and the statistical framework for analyzing the association between workspace clutter and cognitive control.

**Strategic Pivot**: Given the lack of a single public dataset linking *participant-level* Stroop/Flanker performance with *participant-specific* workspace images, the primary strategy is **Synthetic Data Generation** for the purpose of **Pipeline Validation**.

Crucially, the synthetic data generator is designed to **decouple** the generation of visual complexity metrics from cognitive performance scores. Unlike previous iterations that seeded a correlation, this generator creates independent distributions (or introduces latent confounders without forcing a direct predictor-outcome link). This ensures that the statistical analysis is a genuine hypothesis test (which may yield a null result) rather than a tautological verification of a pre-set effect. The primary scientific value of this run is to validate the robustness of the CV and statistical pipeline, not to make empirical claims about human behavior.

## Dataset Strategy

### Verified Datasets & Sources

Per the project constitution and the "Verified datasets" constraint, we rely on the following sources. Note: No single public dataset currently links *participant-level* cognitive scores with *participant-specific* workspace images. Therefore, the plan utilizes a hybrid approach: **Synthetic Generation** for the core analysis (to ensure N≥100 and matched IDs) and **Public Repositories** for validating the visual metric extraction logic.

| Dataset Name | Type | URL / Source | Usage in Plan |
|:--- |:--- |:--- |:--- |
| **Synthetic Participant Data** | Generated | N/A (Local Generation) | **Primary Analysis.** Generates N≥150 records with `participant_id`, `reaction_time`, `accuracy`, and `workspace_image_path`. **Crucially, visual metrics and cognitive scores are generated independently** to avoid tautology. |
| **OpenML Stroop Tasks** | Public | `https://www.openml.org/search?type=data&sort=runs&data_type=tabular&search=stroop` | **Validation.** Used to verify the format and range of reaction time/accuracy metrics if real data is partially available. No participant-image linkage expected. |
| **HuggingFace Datasets** | Public | ` (Search: "cognitive", "attention") | **Validation.** Checked for any recent datasets with cognitive task data. If found, downloaded for metric validation; otherwise, synthetic data is used. |
| **Open Images / COCO** | Public | `https://storage.googleapis.com/openimages/web/index.html` | **Visual Metric Validation.** A subset of images is used to test the OpenCV edge density, entropy, and YOLO object count pipelines to ensure they produce non-zero variance. |

**Note on Data Acquisition**: The plan explicitly **rejects** the use of unverified URLs (e.g., generic `kaggle.com/datasets/` without a specific ID) to prevent the `UnreachableReference` error. All data paths will be resolved via the `datasets` library or direct, verified HTTP endpoints.

### Synthetic Data Generation Protocol

Since no verified linked dataset exists, we will generate synthetic data with the following properties:
1. **N**: 150 participants (buffer for dropouts).
2. **Image Generation**:
 * **Method**: `Pillow` (CPU-based) compositing of random geometric shapes and textures to simulate "workspace" images.
 * **Metadata**: Each image is tagged with `lighting_condition` (low/medium/high), `room_type` (office/living/dining), and `demographic_group` (simulated) to satisfy Constitution Principle VII (Ecological Sampling Integrity).
 * **Independence**: The visual complexity of these images is determined *solely* by the random compositing process, independent of the cognitive scores.
3. **Cognitive Score Generation**:
 * **Variables**: `reaction_time` (Normal(600, 100)) and `accuracy` (Normal(0.9, 0.05)).
 * **Independence**: These are drawn from independent distributions. No correlation is seeded with visual metrics.
 * **Latent Confounders (Optional)**: To test robustness, we may generate a latent variable `room_quality` that influences both image complexity and cognitive scores, but the *direct* link between image metrics and scores remains unseeded.
4. **Goal**: The resulting dataset will likely show **no significant correlation** (null hypothesis). This is the desired outcome for a valid pipeline test, proving the system can correctly identify the absence of an effect.

## Visual Complexity Metric Extraction

### Methodology

1. **Edge Density**:
 * **Method**: OpenCV Canny Edge Detection followed by pixel ratio calculation.
 * **Formula**: $Density = \frac{\text{Edge Pixels}}{\text{Total Pixels}}$
 * **Normalization**: Result scaled to [0, 1].
 * **Rationale**: Standard method for quantifying structural clutter.
2. **Color Entropy**:
 * **Method**: Histogram calculation across RGB channels (or HSV) and Shannon Entropy summation.
 * **Formula**: $H = -\sum p(x) \log_2 p(x)$
 * **Rationale**: Measures color diversity and visual "noise".
3. **Object Count**:
 * **Method**: Pre-trained YOLOv5n (Nano) model (CPU-optimized).
 * **Rationale**: Detects semantic objects (chair, desk, monitor) rather than just edges.
 * **Constraint**: If detection fails or image is invalid, `NaN` is assigned.

### Computational Feasibility
* **Model**: YOLOv5n (Nano) is <5MB and runs efficiently on CPU.
* **Batching**: Images processed in batches to manage memory.
* **Time**: Estimated < 30 seconds per image on CPU; total < 2 hours for 150 images.

## Statistical Analysis Plan

### Primary Analysis
1. **Pearson Correlation**: Compute $r$ and $p$-value for each of the 6 pairs (3 metrics × 2 outcomes).
 * *Expectation*: Given the independent generation, we expect non-significant results (p > 0.05).
2. **Multiplicity Correction**: Apply **Holm-Bonferroni** correction to the 6 p-values (SC-003).
3. **Linear Regression**: For significant pairs ($p_{adj} < 0.05$), fit $Y = \beta_0 + \beta_1 X + \epsilon$. Report $\beta$, 95% CI, and $R^2$.
4. **Collinearity Check**: Compute **VIF** for a multiple regression model with all 3 visual metrics. If VIF ≥ 5, perform PCA and use PC1 as the predictor (FR-012). The resulting PC1 score is stored as `pca_component_1`.

### Robustness & Sensitivity (FR-009, FR-010)
1. **Bootstrap Resampling**: A sufficient number of iterations to generate 95% CIs for correlation coefficients.
2. **Binning Sensitivity**: Re-run correlation on quartile and decile bins of visual complexity. Verify $r$ sign consistency and magnitude stability (< 0.1 change).

### Confounding Control
* **Latent Variables**: If the synthetic generator includes latent confounders (e.g., `room_quality`), the analysis will check for spurious correlations.
* **Covariates**: If metadata (lighting, room type) shows strong association with visual metrics, these will be included as covariates in a secondary model to isolate the "pure" visual complexity effect.

### Assumptions & Limitations
* **Associational Framing**: All claims will be phrased as "association" or "correlation" (SC-002). No causal language.
* **Synthetic Nature**: Results reflect the simulated data. **Crucially, the synthetic images (composited shapes) do not possess the semantic complexity of real home offices.** Therefore, the computed metrics do not measure "visual distraction" in an ecological sense. The primary value is demonstrating the *pipeline* and *methodological rigor* (VIF, Bootstrap) rather than discovering a new psychological effect.
* **Power**: N=150 provides >80% power to detect r=0.25 at $\alpha=0.05$ (two-tailed), assuming a true effect existed. In this null-hypothesis run, power ensures we can confidently reject a false positive.

## Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **Synthetic Data over Real** | No verified linked dataset exists (cognitive + image). Real data would require manual matching (impossible at scale) or result in N < 100. Synthetic data ensures N≥100 and full control over the generation logic to avoid tautology. |
| **Decoupled Generation** | To avoid the "tautological validation" error, visual metrics and cognitive scores are generated independently. This ensures the analysis is a genuine test of the pipeline's ability to detect (or fail to detect) an effect. |
| **YOLOv5n (Nano)** | Balances object detection capability with CPU feasibility. Larger models (v5l/x) would exceed the 6-hour runtime budget on GitHub Actions. |
| **Holm-Bonferroni** | Less conservative than Bonferroni, preserving power while controlling Family-Wise Error Rate for the 6 tests. |
| **PCA Fallback** | Edge density, entropy, and object count are often correlated (cluttered rooms have more edges, colors, and objects). VIF ≥ 5 is a realistic risk; PCA ensures model stability. |
