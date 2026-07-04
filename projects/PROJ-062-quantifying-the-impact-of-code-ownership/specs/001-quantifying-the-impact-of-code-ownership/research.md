# Research Plan: Code Ownership and Quality

## Hypothesis
Higher code ownership concentration (Gini) is associated with higher bug density,
but the relationship may be non-linear or confounded by code churn.

## Data Sources
- **GitHub Repositories**: Selected for activity and Python content.
- **Git Logs**: Commit history for ownership attribution.
- **GitHub Issues**: Bug reports linked via path proximity.

## Metrics
- **Predictors**: Gini, Gini², Code Churn, Cyclomatic Complexity, Size (KLOC), Age.
- **Outcome**: Bug Density (bugs/KLOC).

## Analysis Plan
1. Calculate correlations (Spearman).
2. Check multicollinearity (VIF).
3. Test non-linearity (Quadratic model vs Linear).
4. Perform sensitivity analysis on significance thresholds.

## Limitations
- Associational only (no causal inference).
- Path-based bug linking may be imperfect.
- Sample size limited by API rate limits and compute time.
