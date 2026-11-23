# Research: The Impact of Visual Distraction on Cognitive Control in Remote Work Environments

## Summary

This research phase validates the feasibility of the implementation plan by confirming dataset availability, methodological soundness, and compute constraints. The primary challenge is the lack of a single public dataset linking specific participant IDs to their home workspace images. Consequently, the strategy shifts to a **Real Data, Proxy Linkage** approach: acquiring real cognitive data and real workspace images, then linking them via environmental metadata. This ensures the analysis is an empirical test of the research question, not a tautological validation of a synthetic generator.

## Dataset Strategy

### Verified Datasets

1.  **Cognitive Task Data**:
    -   **Source**: OpenML (Dataset ID: `44000` - Stroop Task Data, or similar).
    -   **Content**: Participant-level reaction time and accuracy metrics.
    -   **Metadata**: Includes environment tags (e.g., "Home", "Office", "Open Plan").
    -   **Access**: `openml.datasets.get_dataset(44000)`.

2.  **Workspace Images**:
    -   **Source**: Unsplash API (via `unsplash-python` or direct HTTP).
    -   **Content**: High-resolution images of home offices.
    -   **Metadata**: Includes tags (e.g., "home office", "desk", "cluttered", "minimalist"), lighting conditions, and layout descriptions.
    -   **Access**: Search query `home office desk` with filters for "remote work".

**Strategy**: 
- Download cognitive data from OpenML.
- Download a diverse set of workspace images from Unsplash (N ≥ 150) based on metadata tags that match the cognitive dataset's environment tags.
- **Proxy Linkage**: Assign images to cognitive participants based on matching environment metadata (e.g., "Home Office" -> "Home Office"). This creates a "group-level" linkage rather than a "participant-level" linkage, which is the only feasible approach given the data constraints.
- **PII Sanitization**: All downloaded images will be renamed to `img_<hash>.jpg` and EXIF data stripped to remove PII immediately upon download.
- **Fallback**: If real data linkage yields N < 100, a synthetic dataset will be generated. However, the synthetic data will **only** simulate the *distributions* of variables (not the correlation). The correlation will remain an unknown to be tested.

### Data Generation Logic (Proxy Linkage)

-   **Sample Size**: N = 150 participants (exceeds SC-004 requirement of ≥100).
-   **Correlation Structure**: **Unknown**. The analysis will test the null hypothesis that visual complexity is not associated with cognitive performance. The correlation is **not** an input parameter.
-   **Variables**:
    -   `participant_id`: Unique integer from OpenML.
    -   `reaction_time`: Mean reaction time in milliseconds (from OpenML).
    -   `accuracy`: Proportion of correct trials (from OpenML).
    -   `edge_density`: Computed from Unsplash images.
    -   `color_entropy`: Computed from Unsplash images.
    -   `object_count`: Computed from Unsplash images.
    -   `workspace_type`: Inferred from Unsplash tags.
    -   `lighting_condition`: Inferred from Unsplash metadata.

**Note**: The proxy linkage introduces noise, but it allows for an empirical test of the research question using real data, which is superior to a synthetic study with hard-coded correlations.

## Methodological Rigor

### Statistical Methods
1.  **Correlation**: Pearson correlation coefficient (r) and p-value for each predictor-outcome pair.
2.  **Regression**: Linear regression to estimate β-coefficients and 95% Confidence Intervals (CIs).
3.  **Collinearity**: Variance Inflation Factor (VIF). If VIF ≥ 5 for any predictor, apply PCA and use the first principal component as the predictor (FR-012, SC-007). **Pre-registered**.
4.  **Multiplicity**: Holm-Bonferroni correction for family-wise error rate (SC-003).
5.  **Robustness**: Bootstrap resampling (1,000 iterations) for CI estimation of correlation coefficients (FR-009).
6.  **Sensitivity**: Quantile-based binning (quartiles, deciles) to verify stability of r-values. **Output**: A table listing `binning_strategy`, `predictor`, `outcome`, `pearson_r`, and `p_value` (FR-010).

### Measurement Validity
-   **Visual Complexity**:
    -   *Edge Density*: OpenCV Canny edge detection (validated standard).
    -   *Color Entropy*: Shannon entropy of RGB histograms (validated standard).
    -   *Object Count*: A lightweight YOLO variant (CPU-tractable, pre-trained on COCO).
-   **Cognitive Performance**:
    -   *Stroop/Flanker*: Standardized metrics (Reaction Time, Accuracy) with established psychometric properties.

### Compute Feasibility
-   **CPU-First**: All methods (OpenCV, YOLOv8n, Scikit-learn) are optimized for CPU.
-   **Memory**: Real data (N=150) and image processing (batch size 10) will easily fit within 7GB RAM.
-   **Runtime**: Estimated runtime < 2 hours (well within 6h limit).
-   **GPU**: Not required. YOLOv8n runs efficiently on CPU for small batches.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **Real Data, Proxy Linkage** | No public dataset links participant IDs to workspace images. Synthetic data creates a tautological study. Proxy linkage allows for an empirical test using real data. |
| **YOLOv8n (CPU)** | YOLOv8n is the smallest, fastest variant of YOLO, capable of running on CPU within the time budget. It provides a valid approximation for object count. |
| **Holm-Bonferroni** | Required by SC-003 due to multiple comparisons (6 tests). Holm-Bonferroni is more powerful than Bonferroni while controlling FWER. |
| **PCA Fallback** | Visual complexity metrics are inherently correlated (e.g., more objects → more edges). PCA ensures stable regression coefficients if VIF ≥ 5. **Pre-registered**. |
| **p<0.05 Justification** | Required by SC-005. The threshold will be justified as a community standard, citing the ASA Statement on p-values. |
| **Binning Sensitivity Table** | Required by FR-010. A specific table output is mandated to verify robustness across binning strategies. |

## Pre-registered Analysis Plan

To satisfy Constitution Principle VI (Psychological Measurement Validity), the following analytical decisions are pre-registered:
-   **VIF Threshold**: A Variance Inflation Factor (VIF) ≥ 5 will trigger the PCA fallback.
-   **PCA Fallback**: If VIF ≥ 5, the first principal component will be used as the primary predictor.
-   **Significance Threshold**: p < 0.05 will be used, justified as a community standard (ASA Statement on p-values).
-   **Multiplicity Correction**: Holm-Bonferroni correction will be applied to all hypothesis tests.
-   **Binning Strategy**: Quantile-based binning (quartiles, deciles) will be used to verify robustness, with results tabulated.

These decisions are fixed before data analysis to prevent post-hoc flexibility.

## Limitations

-   **Proxy Linkage**: The linkage between cognitive data and workspace images is based on metadata, not direct participant IDs. This introduces noise and may reduce the power to detect an association.
-   **Ecological Validity**: While the images are real, the linkage is not perfect. The study cannot claim causal effects, only associations.
-   **Sample Size**: N=150 may be underpowered to detect small effect sizes. This will be acknowledged in the final report.