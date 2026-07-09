# Deviation Log: Cross-Validation Strategy Selection Logic

**Date:** 2023-10-27
**Task Reference:** T023
**Constitution Principle:** VI (Adaptive Methodology based on Data Constraints)

## 1. Decision Context

The project aims to predict plant stress response from proteomic data across three species (Arabidopsis, Rice, Wheat) and three stress conditions (Drought, Salinity, Heat). A critical modeling decision involves the choice of cross-validation (CV) strategy to ensure robust performance estimation without overfitting, particularly given the variability in available sample sizes for specific stress-species combinations.

## 2. Selection Criteria

The choice between **5-Fold Cross-Validation** and **Leave-One-Out Cross-Validation (LOOCV)** is determined strictly by the number of available samples ($n$) for a given training set (specific species + stress condition combination).

### Threshold Definition
- **Threshold ($n_{thresh}$):** 50 samples.

### Decision Logic
1. **Case A: Large Sample Size ($n \geq 50$)**
 - **Strategy:** 5-Fold Cross-Validation.
 - **Rationale:** When $n \geq 50$, the dataset is sufficiently large to support a 5-fold split without significant variance in the performance estimate. 5-fold CV offers a computationally efficient balance between bias and variance, reducing the training time compared to LOOCV while maintaining statistical reliability.
 - **Implementation:** The dataset is split into 5 equal (or near-equal) folds. The model is trained 5 times, each time using 4 folds for training and 1 for validation.

2. **Case B: Small Sample Size ($n < 50$)**
 - **Strategy:** Leave-One-Out Cross-Validation (LOOCV).
 - **Rationale:** When $n < 50$, the dataset is considered "small." A 5-fold split would result in training sets with fewer than 40 samples (e.g., if $n=40$, training size is 32), which may lead to high bias in the model due to insufficient training data per fold. LOOCV maximizes the training data usage ($n-1$ samples per fold), minimizing bias at the cost of higher variance and computational expense. Given the small $n$, the computational cost is negligible.
 - **Implementation:** The model is trained $n$ times, each time leaving out a single sample for validation.

## 3. Implementation Details

This logic is implemented in `code/modeling/train.py` (Task T019).

```python
# Pseudo-code logic from T019
if n_samples >= 50:
 cv_strategy = "5-Fold"
 cv = KFold(n_splits=5, shuffle=True, random_state=config.RANDOM_SEED)
else:
 cv_strategy = "LOOCV"
 cv = LeaveOneOut()
```

## 4. Deviation from Standard Practice

Standard practice in many large-scale omics studies often defaults to 5-fold or 10-fold CV regardless of sample size to save compute time. However, this project deviates from that standard in the $n < 50$ regime to prioritize **bias reduction** in the performance metric ($R^2$). Using 5-fold CV on very small datasets (e.g., $n=20$) would result in a training set of only 16 samples, which is statistically insufficient for training complex models like Random Forests or SVRs without severe underfitting. LOOCV is the necessary deviation to ensure the model actually learns from the available data.

## 5. Verification

The sample size $n$ is calculated dynamically from the input data matrix before the CV loop begins. The decision is logged in `logs/pipeline.log` for every stress-species combination to ensure reproducibility and auditability of the chosen strategy.

## 6. Conclusion

The hybrid CV strategy (5-Fold for $n \geq 50$, LOOCV for $n < 50$) ensures that the model evaluation is statistically robust across the full range of data availability expected in this project, adhering to the principle of adaptive methodology.