# Research Plan: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

## Overview
This research project investigates the comparative efficacy of Morgan and MACCS molecular fingerprints in predicting organophosphate pesticide toxicity using the Tox21 dataset. The study employs 5-fold cross-validation with Greedy Maximal Dissimilarity splits to ensure structural diversity between training and test sets.

## Objectives
1. Filter the Tox21 dataset for organophosphate compounds using SMARTS pattern `[P](=O)([O,SC])[O,SC]`.
2. Generate Morgan (radius=2, 2048 bits) and MACCS (166 bits) fingerprints.
3. Train Random Forest models (100 trees, max_depth=15) for toxicity endpoint prediction.
4. Perform statistical validation via paired t-tests and bootstrap confidence intervals.
5. Analyze feature importance mapping to phosphorus-centered substructures (SC-003).

## Methodology
- **Data Source**: Tox21 dataset from HuggingFace `deepchem/tox21`.
- **Filtering**: SMARTS-based filtering for organophosphates.
- **Splitting**: Greedy Maximal Dissimilarity Split (Tanimoto < 0.85) ensuring test set size >= 20.
- **Modeling**: Random Forest classifiers trained on CPU.
- **Evaluation**: ROC-AUC, Precision-Recall AUC, Balanced Accuracy.
- **Statistics**: Paired t-tests on CV scores, bootstrap 95% confidence intervals.

## Assumptions
- Toxicity labels in the Tox21 dataset are treated as ground truth.
- No external calibration of toxicity thresholds is performed.
- Measurement uncertainty of the original toxicity assays is not recalculated.
- RDKit fingerprint generation is considered the industry-standard calibration method for molecular descriptors.
- The dataset contains sufficient structural diversity to achieve a valid split (>= 20 samples with Tanimoto < 0.85).

## Limitations and Exclusions
### Measurement Uncertainty & Calibration
Per the project's defined Assumptions, **measurement uncertainty was not recalculated** for the toxicity thresholds, and **no external calibration** procedures were performed on the assay data. The toxicity labels from the Tox21 dataset are treated as definitive ground truth for the purpose of model training and evaluation.

The standard deviation of the original toxicity measurements is not available within the provided dataset metadata and was not independently verified. Similarly, the calibration of the fingerprint algorithms relies on the established RDKit implementation, which is the industry-standard for molecular descriptor generation. As such, the analysis assumes the validity of these pre-computed descriptors without further instrumental calibration.

This exclusion is explicitly documented to maintain transparency regarding the scope of the validation. Future work may incorporate uncertainty quantification if raw assay data becomes available.

## Expected Outcomes
- A comparative report detailing ROC-AUC and PR-AUC for both fingerprint types.
- Statistical significance of performance differences (p < 0.05).
- Feature importance analysis linking Morgan fingerprint bits to phosphorus-centered substructures.
- Verification of SC-003 hypothesis regarding feature importance distribution.

## References
- Tox21 Data Challenge: https://tox21.gov/
- RDKit Documentation: https://www.rdkit.org/docs/
- HuggingFace Datasets: https://huggingface.co/docs/datasets