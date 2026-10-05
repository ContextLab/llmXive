# Investigating the Correlation Between Gut Microbiome Composition and Cognitive Decline in Older Adults

## Abstract
[Abstract content to be finalized upon completion of analysis]

## 1. Introduction
[Introduction content]

## 2. Methods

### 2.1 Data Sources
This study utilizes two primary datasets: the American Gut Project (AGP) 16S rRNA gene sequencing data for gut microbiome profiling and the Health and Retirement Study (HRS) for cognitive assessment and demographic covariates.

### 2.2 Data Preprocessing and Rarefaction
To ensure comparability across samples with varying sequencing depths, we applied a rarefaction procedure as specified in FR-002. Raw 16S amplicon sequence data were collapsed to the genus level using the `scikit-bio` library. We then determined the minimum read depth among retained samples (after initial quality filtering) and subsampled all samples to this uniform depth without replacement. This approach mitigates bias introduced by uneven sequencing effort while preserving the relative abundance structure of the microbial community. Following rarefaction, taxonomic counts were converted to relative abundances for downstream analysis.

### 2.3 Covariate Handling
Participant data were filtered to include only individuals aged 60 years or older. Missing values in covariates (BMI, education level) were imputed using median imputation for continuous variables and mode imputation for categorical variables. A strict validation step ensured no null values remained in the final analysis-ready dataset, specifically for the cognitive score and the top 5 most prevalent microbial genera.

### 2.4 Correlation Analysis
To assess associations between microbial abundance and cognitive decline, we employed a two-step statistical approach:
1. **Centered Log-Ratio (CLR) Transformation**: Given the compositional nature of microbiome data, we applied the CLR transformation to the rarefied genus-level abundance table. This transformation maps the data from the simplex to real Euclidean space, allowing for standard correlation calculations while mitigating the closure problem.
2. **Spearman Rank Correlation**: We computed Spearman's rank correlation coefficient ($\rho$) between each CLR-transformed genus abundance and the cognitive test score. This non-parametric method was chosen for its robustness to non-linear relationships and outliers.
3. **Multiple Testing Correction**: To control the false discovery rate (FDR) across the multiple hypothesis tests performed (one per genus), we applied the Benjamini-Hochberg procedure ($\alpha = 0.05$). Associations with an adjusted p-value < 0.05 were flagged as statistically significant and explicitly labeled as "associational" in the results to distinguish them from causal claims.

### 2.5 Predictive Modeling with Nested Cross-Validation
To evaluate the predictive utility of the gut microbiome for cognitive scores, we trained a Random Forest regressor. To prevent data leakage and obtain an unbiased estimate of model performance, we implemented a nested cross-validation (CV) scheme:
- **Outer Loop**: A k-fold cross-validation (k=5) was used to split the data into training and hold-out test sets.
- **Inner Loop**: Within each training fold of the outer loop, a hyperparameter tuning grid search (e.g., number of trees, max depth) was performed using another k-fold CV.

The final model performance was evaluated on the hold-out sets from the outer loop, reporting the coefficient of determination ($R^2$) and Root Mean Squared Error (RMSE).

### 2.6 Robustness and Significance Validation
- **Permutation Testing**: To establish a null distribution for the predictive performance, we performed 1000 permutations of the cognitive scores while keeping the microbial features fixed. The 95th percentile of this null distribution served as the significance threshold.
- **Sensitivity Analysis**: We conducted a sensitivity analysis by varying the rarefaction depth across a range (5000 to minimum depth) to ensure that observed correlations were not artifacts of a specific sequencing depth cutoff.
- **Collinearity Check**: For the top predictive taxa identified by feature importance, we calculated Variance Inflation Factors (VIF) to assess multicollinearity. Pairs with VIF > 5 were flagged for review.

## 3. Results
[Results content to be populated with correlation tables and model metrics]

## 4. Discussion
[Discussion content]

## 5. Limitations
[Limitations content]

## 6. Conclusion
[Conclusion content]

## References
[References to be added]
