## Research-question validation

### Phenomenon-vs-method check

**Verdict**: pass

The question investigates the interaction between data characteristics (collinearity, heteroscedasticity, outliers) and statistical stability (coefficient variance), which is a substantive inquiry into the behavior of OLS estimators in non-ideal conditions. It is framed around the theoretical relationship between these variables rather than the performance of a specific algorithm or computational constraint.

### Circularity check

**Verdict**: pass

The predictors (condition number, heteroscedasticity metrics) are calculated from the full dataset to characterize its properties, while the outcome variable (empirical coefficient variance) is derived from the distribution of estimates across independent random subsets. Since the outcome is generated via resampling rather than being a direct transformation of the full dataset's summary statistics, the relationship is empirical and not mechanically guaranteed.

### Triviality check

**Verdict**: pass

A positive result (violations amplify instability) would provide critical empirical bounds on the reliability of standard errors in messy real-world data, challenging the "textbook" assumptions often applied blindly. A null result (violations do not interact with collinearity as predicted) would be equally surprising and informative, suggesting that OLS is more robust to specific combinations of assumption violations than current theory suggests.

### Question-narrowing check

**Verdict**: pass

The question explicitly names the domain relationship of interest: how assumption violations modify the link between collinearity and stability. It avoids framing the inquiry around whether a specific method can run within a budget or outperform a baseline, focusing instead on the statistical properties of the data and estimator.

### Overall verdict

**Verdict**: validated

All four checks pass, indicating a robust scientific question that investigates the interaction of statistical assumptions without falling into circularity or implementation-focused narrowness. The project is ready to advance to initialization.
