# Research Plan: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## 1. Introduction

This study investigates the predictive performance of Morgan (ECFP) and MACCS molecular fingerprints for classifying organophosphate pesticide toxicity using the Tox21 dataset. [UNRESOLVED-CLAIM: c_9b95f7eb — status=not_enough_info] We aim to determine if the structural specificity of Morgan fingerprints yields statistically significant improvements over the coarser MACCS keys for this chemical class.

## 2. Methodology

### 2.1 Data Acquisition and Filtering
- **Source**: Tox21 dataset from HuggingFace (`deepchem/tox`).
- **Filtering**: Compounds are filtered using the SMARTS pattern `[P](=O)([O,SC])[O,SC]` to isolate organophosphates.
- **Validation**: Labels are validated for binary toxicity endpoints (e.g., NR-AR, NR-ER).

### 2.2 Feature Engineering
- **Morgan Fingerprints**: Radius=2, 2048 bits.
- **MACCS Fingerprints**: 166 bits.
- **Split Strategy**: 5-Fold Greedy Maximal Dissimilarity Split (Tanimoto < 0.85) to ensure structural diversity between training and test sets.

### 2.3 Model Training
- **Algorithm**: Random Forest (100 trees, max_depth=15).
- **Hardware**: CPU-only execution.
- **Validation**: 5-Fold Cross-Validation.

### 2.4 Statistical Evaluation
- **Metrics**: ROC-AUC, Precision-Recall AUC, Balanced Accuracy.
- **Significance Testing**: Corrected Resampled t-test (Nadeau & Bengio) on 5-fold CV scores.
- **Confidence Intervals**: 1,000 bootstrap resamples of the performance difference.

## 3. Response to Reviewer Concerns

**Reviewer**: `marie-curie-simulated`
**Date**: 2026-06-10
**Concern**: "The current methodology does not specify the measurement uncertainty for toxicity thresholds. In chemical work, we must know the precision of our instruments before claiming a substance causes harm. What is the standard deviation of your toxicity measurements? What calibration procedures validate the fingerprint algorithms?"

### 3.1 Measurement Uncertainty and Toxicity Labels
The reviewer correctly notes that in wet-lab chemical analysis, instrument precision and measurement uncertainty (standard deviation) are critical for establishing ground truth. However, this study utilizes the **Tox21 dataset**, which is a curated collection of high-throughput screening (HTS) assay results.

- **Assumption of Ground Truth**: Per the project specification (Spec Assumptions: "Instrument Precision"), the binary toxicity labels (Active/Inactive) provided in the Tox21 dataset are treated as the **ground truth** for the purpose of machine learning model training. The variability inherent in the original HTS assays (e.g., signal-to-noise ratios, Z-scores) has already been processed and thresholded by the original data curators (NCI, NIEHS) into the binary states used here.
- **No Additional Standard Deviation**: The dataset does not provide per-compound standard deviations for the binary classification labels. Introducing fabricated uncertainty values would constitute data fabrication. The "uncertainty" in this study is therefore modeled statistically through the **variance in model performance** across the 5-fold cross-validation splits, rather than through measurement error bars on the input labels.

### 3.2 Algorithm Calibration
Regarding the calibration of fingerprint algorithms:
- **Standard Implementation**: The Morgan and MACCS fingerprints are generated using **RDKit**, a standard, open-source cheminformatics toolkit. The parameters used (Radius=2, 2048 bits for Morgan; 166 bits for MACCS) are the industry-standard defaults widely accepted in computational chemistry literature.
- **Calibration via Validation**: The "calibration" of these descriptors is empirically validated through the **5-Fold Cross-Validation** and the **Corrected Resampled t-test**. If the fingerprints were poorly calibrated for the task, the statistical tests would reveal a lack of predictive power or significant bias. The rigorous statistical comparison (T025a) serves as the validation mechanism for the feature engineering pipeline.

### 3.3 Statistical Rigor
To address the concern regarding the trustworthiness of conclusions:
- The study employs the **Corrected Resampled t-test (Nadeau & Bengio)**, which is specifically designed to account for the variance introduced by both the data splitting process and the learning algorithm. This method is more rigorous than a standard t-test on a single split and provides a robust estimate of whether the observed performance difference between Morgan and MACCS fingerprints is statistically significant.
- **Bootstrap Confidence Intervals** (1,000 resamples) are calculated to quantify the uncertainty in the performance difference (Morgan - MACCS), providing the 95% confidence intervals requested for robust inference.

## 4. Conclusion
This study relies on established, high-quality public data (Tox21) and standard computational chemistry tools (RDKit). The statistical rigor is ensured through robust cross-validation and hypothesis testing, rather than re-calibrating the binary labels themselves. The methodology is transparent, reproducible, and adheres to the constraints of the available data.