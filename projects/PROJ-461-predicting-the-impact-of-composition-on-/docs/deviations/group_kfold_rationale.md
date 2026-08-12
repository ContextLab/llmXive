# Deviation Rationale: Group K-Fold vs. Stratified K-Fold

## Overview
This document outlines the scientific rationale and decision process for deviating from the original specification (FR-003) which mandated **Stratified K-Fold** cross-validation. The proposed implementation replaces this with **Group K-Fold** to prevent data leakage inherent in metallic glass composition datasets.

## Problem Statement: Data Leakage in Composition Data
Metallic glass datasets often contain multiple samples with similar or identical base compositions (e.g., variations in heat treatment or minor alloying elements).

If we use standard Stratified K-Fold:
1. Rows with similar compositions (e.g., `Zr50Cu40Al10` and `Zr51Cu39Al10`) may be split across training and testing sets.
2. The model learns the specific "signature" of that composition family in the training set.
3. When tested on the similar composition in the test set, the model achieves artificially high performance because it has effectively "seen" that composition family before.

This violates the principle of independent and identically distributed (i.i.d.) test data, leading to over-optimistic R² and MAE metrics that do not generalize to truly novel compositions.

## Proposed Solution: Group K-Fold
To mitigate this, we group samples by their **dominant element** (the element with the highest mass fraction).

### Grouping Logic
1. Parse the `composition` column to determine mass fractions.
2. Identify the element with the maximum mass fraction for each row.
3. Assign a `group_id` based on this dominant element (e.g., all Zr-based glasses form one group).
4. Use `GroupKFold` from `sklearn.model_selection` to ensure all samples of a specific dominant element are either entirely in the training set or entirely in the test set for a given fold.

### Scientific Rationale
- **Generalization**: The model must learn physics-based trends (e.g., how atomic radius mismatch affects density) rather than memorizing composition families.
- **Realistic Evaluation**: This simulates the real-world scenario where a researcher proposes a new Zr-based glass and the model must predict its density without having seen *any* Zr-based glasses during training.
- **Robustness**: It prevents the model from exploiting correlations that only exist within a specific chemical system.

## Deviation Details
- **Original Spec (FR-003)**: Stratified K-Fold (k=5) based on density bins.
- **New Implementation**: Group K-Fold (k=5) based on dominant element.
- **Justification**: The stratification by density does not account for compositional similarity. Grouping by dominant element is a more rigorous test of the model's ability to generalize to new chemical systems.
- **Impact**: This may result in lower reported R² compared to Stratified K-Fold, but the metrics will be more trustworthy and indicative of real-world performance.

## Implementation Notes
- The `derive_dominant_element` function in `code/models/train.py` will compute the grouping variable.
- The `GroupKFold` splitter will be used in the training loop.
- This change is pending formal approval via a Kickback Request to update FR-003 in the specification.

## References
- Plan.md: Explicitly notes the deviation to prevent data leakage.
- Scikit-learn Documentation: `sklearn.model_selection.GroupKFold`.
