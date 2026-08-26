# Methodology Documentation

## Data Sources
- **UK Biobank 16S rRNA Sequencing Data**: Gut microbiome composition data from stool samples
- **UK Biobank Cognitive Assessments**:
 - Field 20400: Reaction time
 - Field 20002: Various cognitive tests (as specified in validated instruments)

## Compositional Data Analysis

### Zero-Replacement
Microbiome data contains many zeros due to undersampling. We use **Bayesian-multiplicative replacement** (Martín-Fernández et al., 2003) with prior alpha=1e-6:

This method:
1. Identifies zero counts
2. Replaces zeros with small values proportional to the non-zero composition
3. Maintains the constant-sum constraint of compositional data

### ILR Transformation
Isometric Log-Ratio (ILR) transformation converts compositional data to Euclidean space:

**Formula**:
```
ilr(x) = V' * ln(x)
```
where V is the orthonormal basis matrix constructed via sequential binary partition (SBP).

**Advantages**:
- Orthonormal coordinates (Euclidean geometry applies)
- Subcompositional coherence
- Proper handling of the simplex geometry

## Statistical Analysis

### Linear Models with Confounder Control
We fit linear regression models with the following form:

```
Cognitive_Score ~ ILR_Taxon_1 + ILR_Taxon_2 +... + Age + Sex + BMI + Diet + Activity + Medication
```

### Regularization
- **Lasso (L1)**: Performs feature selection, shrinking less important coefficients to zero
- **Ridge (L2)**: Shrinks coefficients uniformly, useful for multicollinearity

### Multiple Testing Correction
**Benjamini-Hochberg (BH) procedure** controls the false discovery rate (FDR):
1. Sort p-values: p(1) ≤ p(2) ≤... ≤ p(m)
2. Find k such that p(k) ≤ (k/m) * α
3. Reject all hypotheses with p-values ≤ p(k)

## Interaction Analysis
To assess age-dependent effects:

```
Cognitive_Score ~ ILR_Taxon * Age_Group + Confounders
```

where Age_Group is categorical (Younger: <65, Older: ≥65).

## Power Analysis
Power is calculated using:
- Effect size (β): Expected coefficient magnitude
- Sample size (n): Number of participants
- Significance level (α): Typically 0.05
- Number of predictors

**Gate Criterion**: Power ≥ 0.8 required to proceed with real data analysis.

## Sensitivity Analyses
1. **Threshold Sweep**: Evaluate how many taxa are significant at different p-value cutoffs
2. **Over-Control Bias**: Compare models with and without potential mediators (diet, medication)
3. **Model Selection**: Compare Lasso vs Ridge convergence and stability

## Assumptions and Limitations
- Cross-sectional design (cannot infer causality)
- 16S rRNA provides genus-level resolution (not species/strain)
- Residual confounding may exist despite adjustment
- Multiple testing increases false positive risk (mitigated by BH correction)
