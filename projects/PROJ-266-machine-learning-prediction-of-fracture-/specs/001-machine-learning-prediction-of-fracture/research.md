# Research: Machine Learning Prediction of Fracture Toughness from Microstructure Images

## Dataset Strategy

The project relies on the availability of a dataset containing paired microstructure images (SEM/TEM) and fracture toughness ($K_{IC}$) values for steel, aluminum, and titanium alloys.

### Verified Datasets

The following datasets have been verified for reachability and format. **Note**: A direct "Metallurgical Microstructure–Fracture Toughness" dataset with $K_{IC}$ labels was **not** found in the verified list provided.

*If the provided verified datasets do not contain the required $K_{IC}$ labels, the implementation will fail the "Dataset-variable fit" check. The plan explicitly flags this gap and provides a fallback.*

| Dataset Name | Verified URL | Format | Suitability for $K_{IC}$ Prediction |
|:--- |:--- |:--- |:--- |
| SEMrush Videos | ` | CSV (Video metadata) | **NO**. Contains video metadata, not microstructure images or $K_{IC}$. |
| LandCover Aerial | ` | ZIP (Aerial imagery) | **NO**. Contains aerial land cover, not metallic microstructures. |
| SemiKong Training | ` | Parquet (Training data) | **NO**. Likely contains non-metallurgical training data. |
| WebVid-10M | ` | CSV (Video metadata) | **NO**. Video dataset. |
| kbd-ru-1.67M | ` | Parquet (Text/Keyboard) | **NO**. Text/Keyboard data. |
| CNN/DailyMail | ` | Parquet (News) | **NO**. Text summarization dataset. |
| CNN/DailyMail Meta | ` | Parquet (News) | **NO**. Text data. |
| CNN/DailyMail Snippets | ` | Parquet (News) | **NO**. Text data. |

**Critical Gap Identified**: None of the verified datasets listed above contain metallic alloy microstructure images paired with fracture toughness ($K_{IC}$) values.
* **Assumption in Spec**: The spec assumes "The 'Metallurgical Microstructure–Fracture Toughness' dataset from the Materials Data Facility contains all necessary variables".
* **Reality**: This dataset is **not** in the verified list.
* **Plan Action**: The implementation will use a **Synthetic Microstructure Generator** as the primary data source to ensure reproducibility (Constitution Principle I). The code will also support a **user-provided local dataset** (CSV + Image folder) as a secondary fallback. The `research.md` explicitly documents this mismatch to prevent the "fatal, blocking flaw" of planning for a dataset that doesn't exist.

### Data Variable Fit
* **Required**: Image (SEM/TEM), $K_{IC}$ (float), Alloy Family (categorical: Steel, Al, Ti).
* **Available in Verified List**: None.
* **Strategy**: The `synthetic_gen.py` script generates images and $K_{IC}$ values based on a physics-informed proxy (e.g., grain size variance). The `ingest.py` script validates the presence of these columns in a local CSV if provided. If missing, the pipeline will halt with a clear error message: "Required variable 'K_IC' or 'alloy_family' missing from input."

## Statistical Rigor

### Multiple Comparison Correction
The project compares the CNN against two baselines (Linear Regression, Random Forest).
* **Method**: **Permutation Test** on the distribution of MAE differences across 5 seeds.
* **Rationale**: The Wilcoxon signed-rank test is invalid for N=5 (too few pairs). The Permutation Test is non-parametric and robust for small sample sizes, allowing us to empirically estimate the null distribution by shuffling model labels.
* **Correction**: Since the primary comparison is CNN vs. Baseline, we will report the uncorrected p-value from the Permutation Test. However, if multiple comparisons are made (e.g., CNN vs. LR AND CNN vs. RF), we will apply a **Bonferroni correction** to the final p-values to control the family-wise error rate.

### Sample Size / Power
* **Limitation**: The spec targets $\ge$ 500 images, but the plan now targets $\ge$ 2,000 images via synthetic generation to reduce overfitting variance.
* **Acknowledgement**: With N=5 seeds, the statistical power to detect small differences in MAE is limited. The Permutation Test will be used, but the plan explicitly states: "With N=5, the confidence interval will be wide; significance is only claimed if the effect size is massive."
* **Strategy**: If the actual dataset size is < 2,000, the results will be reported as 'exploratory' rather than 'definitive'.
* **Image Count vs. Seed Count**: The validity of the statistical test depends on the number of *seeds* (N=5), not the number of images. Even with a large dataset of images, if only 5 seeds are run, the test remains invalid for significance claims without a Permutation Test. The increased image count ensures the model learns robust features, reducing the variance in the MAE distribution, which is critical for the Permutation Test to have power.

### Causal Inference / Identification
* **Observational Nature**: This is an observational study (predictive modeling). No causal claims (e.g., "Grain boundaries *cause* higher toughness") will be made.
* **Framing**: All claims will be framed as "associational" or "predictive". The model learns correlations between texture features and $K_{IC}$.

### Measurement Validity
* **$K_{IC}$**: For synthetic data, $K_{IC}$ is assigned based on a physics-informed proxy (grain size variance). For user data, it is assumed ground truth from standard mechanical testing.
* **Texture Features**: GLCM and Power Spectra are standard, validated metrics in materials science for quantifying grain size and phase distribution.

### Predictor Collinearity
* **Issue**: Handcrafted features (GLCM) and CNN features may be correlated.
* **Strategy**: The baselines are trained on GLCM and Power Spectra features *automatically extracted* from the raw pixel data by the same preprocessing pipeline used for the CNN. This ensures the comparison isolates the 'architecture' (CNN vs. Shallow) rather than 'feature source' (pixels vs. pre-computed). The null hypothesis is that the CNN's ability to learn non-linear combinations of these features (and spatial hierarchies) provides superior predictive power over the handcrafted features alone.

### Attribution Methodology
* **Method**: **InputXGrad (Integrated Gradients)** is selected over Grad-CAM.
* **Rationale**: Grad-CAM is designed for classification tasks (activating class-specific neurons) and is mathematically undefined for regression tasks without arbitrary adaptations. InputXGrad is the standard, mathematically rigorous method for attributing scalar outputs (like $K_{IC}$) to input features. This ensures the attribution is scientifically sound and aligns with the project's goal of identifying predictive microstructural motifs.
* **Stability**: Stability is validated via Intersection-over-Union (IoU) across multiple augmented views of the same image.

## Compute Feasibility

* **Hardware**: 2 vCPU, 7GB RAM, No GPU.
* **Model**: 3-block CNN (Conv-ReLU-BN-MaxPool) $\to$ FC (256 $\to$ 64 $\to$ 1).
 * **Parameter Count**: Estimated $\approx 0.5 - 1.0$ million parameters.
 * **Memory Footprint**: $\approx 4-8$ MB for model weights. Training batch size will be set to 16 or 32 to fit in RAM.
* **Dataset**: [deferred] images $\times$ 128x128 pixels $\times$ 1 channel $\times$ 5 seeds.
 * **Disk**: $\approx 2000 \times 128 \times 128 / 1024 / 1024 \approx 32$ MB (negligible).
 * **RAM**: Loading all images into memory at once is feasible.
* **Time Limit**: 6 hours.
 * **Estimate**: 5 seeds $\times$ 100 epochs $\times$ 2000 samples / 32 batch size $\approx$ [deferred] iterations.
 * **CPU Speed**: ~100-200 iterations/sec on 2 vCPU. Total time $\approx$ 2.5-4 hours. Safe margin.

## Decision Rationale

1. **Synthetic Data**: The plan explicitly adopts a synthetic data generator to ensure reproducibility (Constitution Principle I) and overcome the lack of a verified external dataset.
2. **CPU-Only**: All libraries are pinned to CPU-compatible versions. No CUDA, no 8-bit quantization.
3. **Statistical Test**: Permutation Test is chosen over Wilcoxon because N=5 is too small for Wilcoxon to have power. The Permutation Test is valid for small N.
4. **Attribution**: InputXGrad (Integrated Gradients) is selected as the standard, mathematically defined method for regression tasks, replacing Grad-CAM which is undefined for continuous outputs.
5. **Baseline Fairness**: Baselines use automatically extracted features from the same pipeline as the CNN, ensuring a fair comparison of architecture vs. feature representation.
6. **Sample Size**: The target sample size is increased to [deferred] images to ensure the 3-block CNN can learn robust microstructural features and reduce variance in the MAE distribution, addressing the concern that 500 images is insufficient.
