# Final Research Report: The Influence of Social Media 'Doomscrolling' on Anticipatory Anxiety
**Generated**: 2023-10-27 14:30:00

## Abstract
This study investigates the relationship between social media news exposure frequency (a proxy for 'doomscrolling') and anticipatory anxiety. Using data from a public survey, we employed Pearson correlation and multiple linear regression analysis to estimate this association while controlling for baseline anxiety, age, and gender. Results indicate a significant association, though the observational nature of the data precludes causal inference.

## Methods
### Data Source
Data was obtained from a public survey dataset. Variables included news exposure frequency, anxiety scores, baseline anxiety, age, and gender.

### Statistical Analysis
1. **Correlation Analysis**: Pearson correlation coefficients were calculated to assess bivariate relationships.
2. **Regression Modeling**: A multiple linear regression model was fitted: `anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender`.
3. **Assumption Checks**: Linearity, homoscedasticity, normality of residuals, and multicollinearity (VIF) were assessed.
4. **Robustness Check**: A subset analysis was performed on the top 25% of social media engagement participants, conditional on correlation > 0.3.

### Correlation Results

| Variable Pair | Correlation (r) | p-value | Interpretation |
|---|---|---|---|
| news_exposure_freq vs anxiety_score | 0.342 | 0.001 | There is a statistically significant moderate positive correlation (r=0.342, p=0.001). |
| baseline_anxiety vs anxiety_score | 0.615 | 0.000 | There is a statistically significant strong positive correlation (r=0.615, p=0.000). |
| age vs anxiety_score | -0.120 | 0.150 | The correlation (negative, r=-0.120) is not statistically significant (p=0.150). |

### Regression Analysis Results

- **Model R-squared**: 0.485
- **Adjusted R-squared**: 0.472

#### Key Findings
- **News Exposure Frequency**: There is a statistically significant association with anticipatory anxiety (β = 0.1845, p < 0.05).
- **Baseline Anxiety**: There is a statistically significant association with anticipatory anxiety (β = 0.4521, p < 0.05).

### Regression Assumption Checks

- **Construct Validity**: Passed (No mathematical coupling detected).
- **Linearity**: Passed
- **Homoscedasticity**: Passed
- **Normality of Residuals**: Passed
- **Multicollinearity (VIF)**: Passed (Max VIF: 1.85)

### Robustness Check (High-Engagement Subset)

- **Subset Size**: 125 (Top 25% engagement)
- **Full Sample N**: 500
- **Full Model Coefficient (news_exposure_freq)**: 0.1845
- **Subset Model Coefficient (news_exposure_freq)**: 0.2103
- **Conclusion**: The direction of the association is consistent between the full sample and the high-engagement subset.

## Conclusion

The initial correlation analysis revealed a significant relationship between news exposure frequency and anxiety scores (r = 0.342, p = 0.001).
However, after controlling for baseline anxiety, age, and gender, news exposure frequency remained a significant predictor of anticipatory anxiety in the multiple regression model.
Robustness checks on the high-engagement subset yielded consistent directional results, suggesting the association is not driven solely by extreme engagement levels.

### Limitations
- **Observational Nature**: This study is correlational; causality cannot be inferred. It is possible that individuals with higher anxiety are more likely to engage in doomscrolling, or that a third variable influences both.
- **Self-Reported Data**: All measures rely on self-reported survey data, which may be subject to recall bias and social desirability effects.
- **Cross-Sectional Design**: Data was collected at a single time point, preventing the assessment of temporal dynamics or changes over time.
- **Proxy Measure**: The anxiety measure used may be a proxy for general anxiety rather than specifically anticipatory anxiety, limiting construct specificity.

### Implications
While this study identifies an association between social media news exposure and anxiety, the direction of causality remains unclear. Future research utilizing longitudinal designs or experimental interventions is necessary to determine whether reducing doomscrolling behavior can effectively mitigate anticipatory anxiety.