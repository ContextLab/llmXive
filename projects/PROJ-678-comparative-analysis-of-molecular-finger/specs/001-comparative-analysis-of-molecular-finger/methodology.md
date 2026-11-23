# Methodology and Constraints

This document details the methodological approach and operational constraints adopted for the comparative analysis of molecular fingerprints for pesticide toxicity prediction. It confirms adherence to the specified training SLA duration and the 5-Fold Cross-Validation protocol defined in the project specification.

## 1. Experimental Design

### 1.1 Dataset Acquisition and Filtering
The study utilizes the Tox21 dataset, a standard benchmark for toxicity prediction, sourced directly from the HuggingFace `deepchem/tox21` repository. To focus the analysis on the specific chemical class of interest, a strict SMARTS-based filtering protocol was applied:
- **Target Pattern**: Organophosphates defined by the SMARTS pattern `[P](=O)([O,SC])[O,SC]`.
- **Filtering Logic**: Only compounds matching this pattern were retained for downstream analysis.
- **Data Integrity**: All data processing steps were performed on real, observed chemical structures. No synthetic data generation or placeholder values were introduced at any stage.

### 1.2 Feature Representation
Two distinct fingerprinting methods were implemented to evaluate structural encoding efficacy:
- **Morgan Fingerprints**: Circular fingerprints generated with a radius of 2 and a bit vector length of 2048.
- **MACCS Keys**: Structural keys comprising 166 bits.
- **Implementation**: Fingerprint generation was performed using the RDKit library, adhering to industry-standard parameterization.

## 2. Model Training and Validation Protocol

### 2.1 Cross-Validation Strategy
To ensure robust statistical evaluation, a **5-Fold Greedy Maximal Dissimilarity Split** was employed. This approach prioritizes structural diversity between training and test sets:
- **Threshold**: A Tanimoto similarity threshold of 0.85 was enforced.
- **Algorithm**:
 1. Initialize the test set with the compound furthest from the mean of the dataset.
 2. Iteratively select compounds with the maximum minimum-distance to the current test set.
 3. Include a compound in the test set only if its distance to all existing test set members exceeds the threshold.
- **Validation**: Execution halts if a valid split (minimum 20 samples per test set with Tanimoto < 0.85) cannot be achieved, preventing biased evaluation.

### 2.2 Model Architecture and Training SLA
- **Algorithm**: Random Forest Regressor/Classifier.
- **Hyperparameters**: 100 trees, maximum depth of 15.
- **Hardware Constraints**: Training is strictly CPU-bound. No GPU acceleration or CUDA operations are utilized.
- **SLA Adherence**: The entire pipeline (data loading, fingerprinting, splitting, training, and evaluation) is optimized to complete within a **60-minute window** on a standard 2-core CPU CI environment. This constraint was verified during the development of the `code/train.py` and `code/split.py` modules, which include batched processing and memory-aware operations to ensure compliance.

## 3. Statistical Analysis

### 3.1 Performance Metrics
Models were evaluated using:
- ROC-AUC (Receiver Operating Characteristic Area Under Curve)
- PR-AUC (Precision-Recall Area Under Curve)
- Balanced Accuracy

### 3.2 Significance Testing
- **Paired t-test**: Applied to the 5-fold CV scores for both ROC-AUC and PR-AUC to determine statistical significance (p < 0.05) of the performance difference between Morgan and MACCS fingerprints.
- **Bootstrap Confidence Intervals**: 95% confidence intervals were generated via bootstrap resampling of the performance differences. [UNRESOLVED-CLAIM: c_b2cabf53 — status=not_enough_info]

## 4. Constraints and Assumptions

- **Measurement Uncertainty**: Consistent with the project specification's "Assumptions" section, measurement uncertainty for toxicity thresholds was not recalculated. Toxicity labels from the Tox21 dataset are treated as ground truth. [UNRESOLVED-CLAIM: c_50550d86 — status=not_enough_info]
- **Calibration**: RDKit fingerprint generation is accepted as the industry-standard calibration method; no external calibration procedures were applied.
- **Sample Size Handling**: If the filtered dataset yields fewer than 50 samples, statistical tests (t-tests) are skipped in favor of descriptive statistics, with a warning logged to `filter_log.txt`.
- **Reproducibility**: All random seeds are fixed to 42 to ensure deterministic results across runs. [UNRESOLVED-CLAIM: c_ca4dfa6d — status=not_enough_info]