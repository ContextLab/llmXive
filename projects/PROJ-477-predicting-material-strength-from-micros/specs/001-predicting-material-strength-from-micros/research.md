# Research: Predicting Material Strength from Microstructure Images

## 1. Problem Statement & Hypothesis

**Hypothesis**: Microstructure morphology (grain size, boundary orientation) captured in 2D **synthetic** EBSD images contains sufficient signal to predict macroscopic yield strength, outperforming a naive statistical baseline (mean predictor) and providing interpretable feature importance.

**Null Hypothesis ($H_0$)**: The CNN model's Mean Squared Error (MSE) is not significantly lower than the naive mean predictor's MSE ($\alpha = 0.05$).

**Alternative Hypothesis ($H_1$)**: The CNN model's MSE is significantly lower than the naive mean predictor's MSE.

**Scope Clarification**: This study validates predictive capability on *synthetic* microstructure morphology. Generalization to real-world experimental EBSD is a future work, as the verified dataset source is synthetic. The hypothesis is strictly limited to the synthetic domain to ensure data-variable fit.

## 2. Dataset Strategy

### Verified Datasets
The plan relies exclusively on the following verified source, as mandated by the `# Verified datasets` block:

| Dataset Name | Description | Verified URL | Usage |
|:--- |:--- |:--- |:--- |
| **EBSD Synthetic** | Synthetic EBSD maps with paired yield strength values. | ` | Primary source for training, validation, and testing. Contains a verified set of images (N=2,697). |

**Data Availability Check**:
- **Access**: Public, direct download via HTTPS. No credentials required.
- **Format**: ZIP archive containing images and metadata (CSV/JSON).
- **Variables**:
 - *Input*: 2D EBSD image (grain structure).
 - *Target*: Yield Strength (MPa).
 - *Covariates*: Grain size (extracted via image processing if not explicitly provided).
- **Feasibility**: The dataset size fits within the 7GB RAM and 14GB disk constraints when processed in batches. Streaming is not strictly required but will be used for robustness.

**Dataset-Variable Fit**:
The dataset contains the required predictor (EBSD image) and outcome (Yield Strength). No external variables (e.g., post-task anxiety) are needed. The plan explicitly verifies the presence of strength labels in the manifest before training.

### Data Labeling Strategy
The labels (Yield Strength) are provided directly in the dataset manifest. The dataset size is N=2,697 (source: 2506.09162). The power analysis confirms that with N=2,697, the study is well-powered to detect small effects (e.g., R²=0.05). The risk is detecting a statistically significant but scientifically trivial effect. Therefore, the plan defines a Minimum Effect Size of Interest (MESI) of R² = 0.2.

## 3. Methodology & Statistical Rigor

### 3.1 Model Architecture
- **Base Model**: MobileNetV2 (frozen ImageNet weights) or ResNet-18 (frozen).
- **Head**: Global Average Pooling + Fully Connected Layer (Input: 1280/512, Output: 1).
- **Training**: Transfer learning with frozen backbone to reduce parameters and memory footprint (FR-002).
- **Augmentation**: Random rotation, horizontal flip, brightness adjustment (FR-003).

### 3.2 Statistical Analysis Plan
- **Metrics**: Mean Squared Error (MSE), R² Score (FR-004).
- **Baseline Comparison**:
 - *Naive Baseline*: Constant predictor equal to the mean of the training set yield strength.
 - **Test**: **Paired t-test** on the difference of squared errors ($d_i = e_{cnn, i}^2 - e_{base, i}^2$). The test statistic is $t = \frac{\bar{d}}{s_d / \sqrt{n}}$, where $d$ is the difference vector. This tests if the mean difference is significantly less than zero.
 - *Correction*: **Bonferroni Correction** applied if multiple architectures (MobileNetV2 vs ResNet-18) are trained and compared. Primary model (MobileNetV2) uses $\alpha=0.05$; secondary models use $\alpha/2$.
- **Power Analysis**:
 - **MESI**: Minimum Effect Size of Interest defined as $R^2 = 0.2$.
 - **Limitation**: With N=2,697, the study is well-powered for small effects (detecting R²=0.05 is trivial). The risk is detecting a statistically significant but scientifically trivial effect. The plan distinguishes between statistical significance ($p < 0.05$) and practical significance ($R^2 \ge 0.2$).
- **Causal Inference**:
 - *Observational*: The data is observational (synthetic). Claims are strictly associational. No causal claims regarding microstructure causing strength are made beyond the predictive correlation.
- **Collinearity**:
 - *Check*: If grain size is used as a separate predictor, collinearity with image features is acknowledged. The plan focuses on the image as the primary predictor to avoid definitionally related variables.

### 3.3 Interpretability
- **Method**: Grad-CAM (Gradient-weighted Class Activation Mapping) to highlight regions of the image driving predictions (FR-006).
- **Validation**: **Pearson Correlation** between Grad-CAM activation intensity and extracted grain size. This is physically grounded in the Hall-Petch relationship (strength depends on grain size). We reject the invalid "IoU with boundaries" metric as boundaries are not the sole driver of strength and manual annotation is unavailable.
- **Sensitivity**: Threshold sweep around the median predicted strength to analyze False Positive/Negative rates (FR-007).
- **Uncertainty**: **Monte Carlo (MC) Dropout** used to generate confidence intervals for individual predictions (FR-008).

## 4. Compute Feasibility & Resource Plan

### CPU-First Strategy
- **Environment**: GitHub Actions Free Tier (2 vCPU, ~7GB RAM).
- **Optimization**:
 - Frozen backbone reduces compute load.
 - Batch size tuned to fit RAM (e.g., 16-32).
 - Mixed precision (AMP) disabled to avoid GPU dependency; standard float32 used.
 - Early stopping (patience=5) to prevent unnecessary epochs.
- **GPU Escape Hatch**:
 - If the CPU run fails due to memory or time limits (unlikely for MobileNetV2 with frozen weights), the plan triggers a scaled-down run on a Kaggle GPU (sufficient VRAM for model training).
 - *Scaling*: Reduce batch size or number of epochs if needed.
 - *Note*: No synthetic stand-ins are used; the real model is run on the scaled GPU.

### Data Processing Order
1. **Download & Verify**: Fetch dataset, compute checksum, validate manifest.
2. **Preprocess**: Resize, normalize, split (Train/Val/Test).
3. **Feature Extraction**: Extract grain size if required (FR-009).
4. **Train**: Fit CNN with augmentation.
5. **Evaluate**: Compute metrics, run paired t-test, generate reports.
6. **Interpret**: Generate Grad-CAM and sensitivity analysis.

## 5. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **MobileNetV2 (Frozen)** | Lightweight architecture ensures CPU feasibility. Frozen weights prevent overfitting on small dataset. |
| **Naive Mean Baseline** | Standard null hypothesis for regression tasks. Directly tests if image features add signal. |
| **Paired t-test** | Appropriate for comparing paired errors (CNN error vs. Baseline error for each sample). |
| **Grad-CAM** | Computationally cheaper than SHAP for CNNs; sufficient for identifying morphological drivers. |
| **MC Dropout** | Standard method for estimating predictive uncertainty in deep learning. |
| **Verified HuggingFace Source** | Ensures reproducibility and avoids access-gated data (fatal flaw). |
| **Synthetic Scope** | Aligns hypothesis with the available verified dataset to avoid methodological flaws. |

## 6. Risk Mitigation

- **Data Corruption**: `validate.py` checks for invalid pairs (missing metadata, NaN) and aborts if >1% invalid (US-1, AC-3).
- **Memory Overflow**: Batch loading strategy implemented; if RAM exceeds 7GB, job fails gracefully with error.
- **Model Non-Convergence**: Early stopping halts training if validation loss increases; best checkpoint retained.
- **Baseline Outperformance**: If CNN fails to beat baseline, the result is reported as "Not Significant" (null hypothesis accepted), not fabricated.
- **Statistical Validity**: Paired t-test and Bonferroni correction ensure valid inference.