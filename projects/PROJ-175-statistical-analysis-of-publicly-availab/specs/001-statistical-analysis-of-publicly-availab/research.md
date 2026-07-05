# Research: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

## 1. Research Question & Hypothesis

**Primary Question**: Do semantic/flavor similarity and functional roles predict culinary compatibility between ingredient pairs *beyond* what is explained by co-occurrence frequency alone?

**Hypothesis**:
- $H_1$: The full model (Frequency + Semantic Similarity + Orthogonalized Role) will have a significantly higher AUC than the null model (Frequency only) ($\Delta AUC \ge 0.05$, $p < 0.05$).
- $H_2$: Semantic similarity and orthogonalized functional role will have statistically significant coefficients ($p < 0.05$) in the regularized logistic regression, after controlling for multicollinearity (VIF < 5).

## 2. Dataset Strategy

We utilize distinct datasets to ensure statistical independence between predictors and outcomes. **Note**: Execution halts if any dataset is unverified.

| Dataset | Purpose | Source / URL | Verification |
|:--- |:--- |:--- |:--- |
| **Recipe1M (Text Embeddings)** | Derive co-occurrence frequencies, semantic similarity, and functional roles. | ` | **Verified**: Parquet format. Contains text embeddings. |
| **Counterfactual Recipe Generation** | Provide independent binary compatibility labels (sensory scores). | *NO VERIFIED SOURCE FOUND in provided block.* | **Critical**: Pipeline halts at Phase 0.1 if this dataset cannot be located via a verified loader (e.g., `datasets.load_dataset("counterfactual-recipes")` if it exists) or a verified URL. No analysis proceeds without verified outcome labels. |

**Dataset Strategy Note**:
- **Recipe1M**: Used for $C_{ij}$ (co-occurrence) and semantic similarity (via text embeddings, as chemical vectors are not available in verified sources).
- **Counterfactual**: Used for $Y$ (compatibility). **Constraint**: If no verified source exists, the project cannot validate the hypothesis and will report a "Data Availability Failure".

## 3. Methodology

### 3.1 Data Pre-processing
1. **Ingestion**: Stream Recipe1M parquet files. Do not load full dataset into RAM.
2. **Normalization**: Map ingredient names to canonical IDs using text embedding similarity (cosine) + Levenshtein distance $\le 2$.
3. **Co-occurrence**: Construct sparse matrix $C$. Apply log-transform: $\log(C_{ij} + 1)$.
4. **Semantic Similarity**: Compute cosine similarity between text embedding vectors.
 - **Missing Data Handling**: If a pair lacks embedding data, impute with the **global median** similarity and set a `is_missing_similarity` flag to 1. This allows sensitivity analysis on the imputation bias.
5. **Functional Role (Orthogonalized)**:
 - Calculate raw rank of ingredient in the list (1st, 2nd, etc.).
 - Regress `Rank` on `Global Log-Frequency` of the ingredient.
 - Use the **Residuals** of this regression as the 'Functional Role' predictor.
 - **Rationale**: This explicitly removes the variance in 'Role' that is explained by 'Frequency', ensuring the predictors are statistically orthogonal for the LRT (addressing tautology concerns).
6. **Labeling**: Join with Counterfactual dataset to get binary compatibility label. **Halt** if join fails due to missing labels.

### 3.2 Statistical Modeling
1. **Power Analysis**: Calculate required $N$ for effect size 0.1. If $N$ exceeds RAM, downsample to max feasible $N$ and record achieved power.
2. **Multicollinearity Check**: Calculate VIF for all predictors.
 - **Decision**: If VIF > 5 for 'Role', drop 'Role' and re-test $H_1$ with only 'Semantic Similarity'.
3. **Model 1 (Null)**: Logistic Regression with only `log_co_occurrence`.
4. **Model 2 (Full)**: Logistic Regression with `log_co_occurrence`, `semantic_similarity`, `orthogonalized_role`, `is_missing_similarity`.
5. **Model 3 (Bayesian)**: Hierarchical Bayesian model with ingredient-level random effects (PyMC, CPU).
6. **Hypothesis Test**: Likelihood-ratio test between Model 1 and Model 2.

### 3.3 Evaluation
1. **Metrics**: AUC, Precision, Recall, Calibration Plot.
2. **Hypothesis**: Test if $\Delta AUC \ge 0.05$ is significant.
3. **Sensitivity Analysis**: Compare model coefficients between 'Median Imputation' and 'Missing Indicator' only models to assess bias.

## 4. Statistical Rigor & Constraints

- **Multiple Comparisons**: If testing multiple functional roles, apply Bonferroni correction or FDR.
- **Power Analysis**: Target effect size of practical significance. If underpowered, report as limitation.
- **Causal Inference**: Observational study. Claims limited to association.
- **Measurement Validity**: Text embeddings are proxies for flavor; acknowledged limitation.
- **Collinearity**: Explicitly check VIF. If 'Role' is dropped, the hypothesis is re-framed to test 'Semantic Similarity' only.

## 5. Compute Feasibility

- **RAM**: Stream data; use `pandas` chunking. Downsample to a representative subset of pairs for modeling.
- **CPU**: Logistic regression is fast. Bayesian sampling (PyMC) limited to a moderate number of samples on a CPU subset.
- **Time**: Pipeline split into phases. Data download, Preprocessing, Modeling, and Evaluation.

## 6. Decision Log

- **Decision**: Use **Orthogonalized Rank** for Functional Role. **Rationale**: Breaks tautology with co-occurrence frequency, ensuring valid LRT.
- **Decision**: Use **Text Embeddings** for Similarity. **Rationale**: Chemical vectors (FlavorDB) not available in verified sources; text embeddings are a verified proxy.
- **Decision**: Use **Median Imputation + Missing Indicator**. **Rationale**: Reduces bias compared to hard zero; allows sensitivity analysis.
- **Decision**: **Hard Fail** on missing Counterfactual dataset. **Rationale**: Prevents circularity and fabrication of outcome labels.