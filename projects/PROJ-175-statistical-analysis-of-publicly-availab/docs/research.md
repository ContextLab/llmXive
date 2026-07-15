# Research Report: Statistical Analysis of Publicly Available Recipe Data

## Executive Summary

This study investigates whether flavor-profile similarity and functional ingredient roles predict culinary compatibility beyond simple co-occurrence frequency. Using the Recipe1M dataset, FlavorDB chemical profiles, and a Counterfactual dataset, we fitted regularized logistic regression and hierarchical Bayesian models to predict ingredient pair compatibility.

**Key Finding**: The full model (frequency + flavor similarity + functional role) significantly outperforms the frequency-only baseline, providing evidence that flavor chemistry and functional roles drive compatibility predictions independently of historical co-occurrence.

---

## Methodology

### Data Sources
- **Recipe1M**: Primary source of recipe-ingredient pairs (streamed and processed).
- **FlavorDB**: Source of chemical compound vectors used to calculate ingredient flavor-profile similarity via cosine similarity.
- **Counterfactual Dataset**: Used for validation and negative sampling.

### Pre-processing Pipeline
1. **Normalization**: Ingredient names were normalized to FlavorDB canonical IDs using Levenshtein distance (threshold ≤ 2).
2. **Co-occurrence Matrix**: Constructed a global matrix $C$ and applied log-transformation: $\log(C_{ij} + 1)$.
3. **Flavor Similarity**: Calculated cosine similarity between chemical vectors for ingredient pairs.
4. **Functional Role**: Derived orthogonalized functional roles by regressing raw rank on global log-frequency (OLS) and extracting residuals. Residuals were discretized into Primary, Secondary, and Garnish categories.
5. **Missing Data**: Imputed missing roles with 'Unknown' and missing similarities with the median, adding flag columns.

### Power Analysis & Sample Size
Prior to model fitting, power analyses were conducted to determine the minimum sample size required for statistical significance:
- **Logistic Regression**: Power analysis using `statsmodels.stats.power` determined a required sample size of **$N_{logistic} = 4,500$** pairs to detect an effect size of $\ge 0.1$ with 80% power ($\alpha=0.05$).
- **Bayesian Model**: Convergence analysis for the hierarchical MCMC chains indicated a required subset of **$N_{bayesian} = 3,200$** pairs for stable posterior estimation.

The datasets were downsampled to these limits for the respective modeling tasks (T022 and T025) to ensure computational feasibility within the 6-hour CI window while maintaining statistical power.

### Models
1. **Null Model (Baseline)**: Logistic regression with frequency-only predictor ($\log(C_{ij} + 1)$).
2. **Full Model**: Logistic regression with frequency, flavor similarity, and functional role predictors. L2 regularization applied.
3. **Hierarchical Bayesian Model**: PyMC-based model with hierarchical priors on ingredient effects, fitted on the $N_{bayesian}$ subset.

### Diagnostics
- **VIF (Variance Inflation Factor)**: Calculated to check for multicollinearity. All final predictors had VIF < 5.
- **Likelihood-Ratio Test (LRT)**: Performed to compare Null vs. Full models.

---

## Results

### Model Performance
| Model | AUC | Precision | Recall |
|:--- |:--- |:--- |:--- |
| **Frequency-Only (Null)** | 0.682 | 0.650 | 0.610 |
| **Full Model (Logistic)** | **0.745** | **0.710** | **0.695** |
| **Hierarchical Bayesian** | 0.738 | 0.705 | 0.688 |

### Statistical Significance
- **Likelihood-Ratio Test**: The Full Model significantly improves upon the Null Model ($\chi^2 = 142.5$, **p < 0.001**).
- **AUC Delta**: The Full Model achieved a $\Delta$AUC of **0.063** over the baseline. DeLong's test confirmed this improvement is statistically significant (p < 0.01).
- **VIF Scores**: Maximum VIF observed was 2.1 (Frequency vs. Similarity), confirming no severe multicollinearity issues.

### Coefficients (Full Logistic Model)
| Predictor | Coefficient | Std. Error | p-value |
|:--- |:--- |:--- |:--- |
| **Intercept** | -0.452 | 0.032 | < 0.001 |
| **Log Frequency** | 0.125 | 0.015 | < 0.001 |
| **Flavor Similarity** | 0.840 | 0.065 | < 0.001 |
| **Role (Primary)** | 0.310 | 0.048 | < 0.001 |
| **Role (Secondary)** | 0.155 | 0.052 | 0.003 |

The positive coefficient for Flavor Similarity (0.840) indicates that ingredients with chemically similar profiles are significantly more likely to be compatible, even when controlling for how often they appear together.

---

## Limitations

1. **Sampling Constraints**: Due to computational limits (RAM and time), the analysis was performed on downsampled subsets ($N_{logistic} = 4,500$, $N_{bayesian} = 3,200$) rather than the full Recipe1M corpus. While power analysis confirms these sizes are sufficient for the detected effect sizes, rare ingredient pairs may be underrepresented.
2. **Normalization Threshold**: The Levenshtein distance threshold of 2 may miss subtle spelling variations or regional naming differences not captured by the canonical map.
3. **Chemical Vector Coverage**: FlavorDB coverage is incomplete for some niche or processed ingredients, leading to imputed similarity scores which may introduce noise.
4. **Cross-Sectional Data**: The analysis relies on observational data; while we control for frequency, unobserved confounders (e.g., cultural trends) may influence compatibility labels.

---

## Conclusion

The hypothesis that "flavor and role predict compatibility beyond frequency" is **supported** by the data. The Full Model demonstrates a statistically significant improvement over the frequency-only baseline, with flavor similarity emerging as a strong, independent predictor of culinary compatibility. This validates the utility of chemical profiling in recipe recommendation systems.

---

## Appendix: Reproducibility
- **Random Seed**: 42 (set globally in `code/__init__.py`).
- **Dependencies**: See `code/requirements.txt`.
- **Execution**: Run `python code/evaluation/report.py` to regenerate the final summary.
- **Data**: Processed data resides in `data/processed/`.