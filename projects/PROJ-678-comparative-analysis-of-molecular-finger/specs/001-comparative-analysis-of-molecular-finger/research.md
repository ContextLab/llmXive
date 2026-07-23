# Research Plan: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## 1. Introduction
This study investigates the predictive performance of different molecular fingerprint representations (Morgan vs. MACCS) for identifying organophosphate toxicity in the Tox21 dataset. The primary goal is to determine if structural fingerprints centered on phosphorus chemistry (Morgan) outperform general structural keys (MACCS) in a machine learning context.

## 2. Methodology
The analysis follows a rigorous pipeline: data acquisition from the Tox21 benchmark, SMARTS-based filtering for organophosphates, fingerprint generation, 5-fold Greedy Maximal Dissimilarity splitting (Tanimoto < 0.85), and Random Forest model training. Performance is evaluated using ROC-AUC and Precision-Recall AUC, with statistical significance assessed via the Corrected Resampled t-test (Nadeau & Bengio).

## 3. Assumptions and Constraints
This section explicitly documents the methodological boundaries regarding measurement uncertainty and calibration, as defined in `spec.md`.

### 3.1 Instrument Precision
The toxicity labels in the Tox21 dataset are binary (active/inactive) assay results derived from high-throughput screening. These labels are treated as ground truth for the purpose of this machine learning study. **Measurement uncertainty was not recalculated, and no standard deviations for toxicity measurements are provided**, as the dataset does not contain continuous quantitative values. This approach is consistent with the project's assumptions regarding the nature of the input data.

### 3.2 Algorithm Calibration
The fingerprint generation algorithms (Morgan and MACCS) utilize the default parameters and implementations provided by the RDKit cheminformatics toolkit. **No external calibration procedures were performed** on these algorithms. RDKit's implementation is considered the industry-standard calibration method for molecular fingerprinting in computational chemistry. The "calibration" of the models is inherent to the standard library implementation and the training data itself.

## 4. Statistical Analysis
To ensure robust conclusions, we employ the Corrected Resampled t-test to compare the performance of Morgan and MACCS-based models across 5 folds. This method accounts for the variance introduced by both the data split and the learning algorithm, providing a more rigorous assessment than a standard t-test on cross-validation scores.

## 5. Expected Outcomes
We anticipate that the Morgan fingerprints, with their ability to capture local substructural environments around the phosphorus center (radius=2), will demonstrate superior predictive performance compared to the fixed-length MACCS keys, particularly in the context of the specific chemical space of organophosphates.

## 6. Limitations
This study is limited by the binary nature of the toxicity labels, which precludes the analysis of dose-response relationships. Furthermore, the generalizability of the findings is constrained to the chemical diversity present within the filtered Tox21 organophosphate subset.

## 7. Response to Reviewer Concerns
In response to the reviewer's query regarding "measurement uncertainty" and "calibration":
- **Measurement Uncertainty**: As noted in Section 3.1, the study treats binary assay labels as ground truth. Recalculating uncertainty is not applicable to binary classification inputs derived from public high-throughput screening data where continuous measurements are unavailable.
- **Calibration**: As noted in Section 3.2, the fingerprint algorithms rely on the standard RDKit implementation. No re-calibration of the fingerprinting process was performed, as the RDKit defaults constitute the accepted standard for this type of analysis. The statistical rigor of the study is ensured by the Corrected Resampled t-test applied to the model predictions, which accounts for variance in the learning process.