---
field: chemistry
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Molecular Topology and Reaction Selectivity

**Field**: chemistry

## Research question

Can topological indices (e.g., Wiener, Balaban) quantitatively predict regioselectivity outcomes in electrophilic aromatic substitution reactions?

## Motivation

Existing models rely heavily on electronic descriptors (HOMO/LUMO) and steric bulk to predict reactivity. Global molecular topology offers a complementary, computationally cheap perspective that may capture long-range structural influences on reactivity without requiring expensive quantum mechanical calculations.

## Related work

TODO — lit-search returned no results.

## Expected results

We expect to find statistically significant correlations (p < 0.05) between specific topological indices and ortho/para/meta product ratios. This would demonstrate that shape descriptors add predictive value beyond standard electronic parameters, potentially enabling faster screening of reaction conditions.

## Methodology sketch

- **Data Acquisition**: Download the USPTO-50k dataset (Lowe et al., 2017) from `https://figshare.com/articles/dataset/USPTO_50k_dataset/4765422`.
- **Reaction Filtering**: Parse SMILES strings to identify electrophilic aromatic substitution reactions using pattern matching on aromatic rings.
- **Descriptor Calculation**: Use `rdkit` (Python) to compute Wiener index, Balaban index, and Zagreb indices for reactant molecules (CPU-efficient graph operations).
- **Label Extraction**: Extract reported yield ratios or major/minor product classifications from the dataset metadata to define selectivity targets.
- **Statistical Modeling**: Perform multiple linear regression and Random Forest regression using `scikit-learn` to correlate indices with selectivity.
- **Validation**: Apply 5-fold cross-validation to assess model performance (R², RMSE) and prevent overfitting.
- **Resource Compliance**: All steps are CPU-bound and will execute within the 7 GB RAM / 6-hour GitHub Actions limit without GPU acceleration.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A.
- Verdict: NOT a duplicate.
