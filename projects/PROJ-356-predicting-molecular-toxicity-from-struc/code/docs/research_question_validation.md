# Research Question Validation

## Original Question
Do explicit structural motifs explain variance in mutagenicity outcomes compared to global molecular descriptors?

## Validation Standard
As emphasized by Marie Curie's review, chemical science demands evidence established through:

1. **Repetition**: Validation requires 5-fold stratified cross-validation repeated 3 times (15 total folds).
2. **Quantification**: Dataset must contain N > 1000 compounds from verified assays.
3. **Specificity**: The assay source must be explicitly identified (e.g., PubChem AID 1851, Ames test).

## Methodology
- **Rule-Based Model**: Scoring based on curated SMARTS patterns with assigned weights
- **Descriptor Model**: Logistic Regression with 20 non-correlated molecular descriptors
- **Statistical Test**: DeLong's test on Out-of-Fold predictions for AUC comparison
- **Error Analysis**: Murcko scaffold extraction from false negatives

## Expected Outcomes
- Quantitative comparison of ROC-AUC and F1 scores
- Statistical significance determination (p < 0.05)
- Identification of missing structural motifs in rule-based system

## Reproducibility
All experiments are reproducible via the pipeline script with fixed random seeds and verified data sources.