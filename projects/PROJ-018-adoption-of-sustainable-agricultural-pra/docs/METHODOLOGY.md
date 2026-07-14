# Methodology: Adoption of Sustainable Agricultural Practices

## 1. Study Design

This study employs a cross-sectional analysis of survey data to estimate the association
between community-engagement intensity and the adoption of sustainable agricultural practices
in low-income areas. The analysis controls for key covariates including farm size, education,
and credit access.

## 2. Data Acquisition and Preprocessing

### 2.1 Source Data
Data is acquired from the World Bank LSMS or FAO FIES repositories. In the event of API
unavailability, a synthetic dataset is generated using `code/00_generate_synthetic_data.py`
to maintain pipeline integrity.

### 2.2 Cleaning Procedures
- **Missing Value Handling**: Rows with >30% missingness in required variables are dropped.
 Remaining missing values are imputed using median (numeric) or mode (categorical) strategies.
- **Normalization**: Categorical codes are standardized to integer representations.
- **Validation**: Schema validation ensures all required fields (age, education, farm_size,
 credit, adoption, engagement items) are present before processing.

## 3. Feature Engineering

### 3.1 Adoption Indicator (`adoption_binary`)
A binary variable is constructed where `1` indicates the respondent reports adopting at least
one sustainable agricultural practice, and `0` otherwise.

### 3.2 Community Engagement Score (`engagement_score`)
A composite index is constructed using a weighted sum or equal-weight average of proxy variables:
- Membership in farmer groups
- Access to extension services
- Participation in collective action
- Knowledge exchange frequency

**Reliability & Validity Checks**:
- **Cronbach's Alpha**: Calculated to assess internal consistency.
- **Exploratory Factor Analysis (EFA)**: Performed using Principal Axis Factoring extraction
 with Varimax rotation. Factors are retained based on Kaiser's rule (eigenvalues > 1).
- **Convergent Validity**: Checked via correlation with theoretically related constructs.
- All metrics are serialized to `results/validity_metrics.yaml`.

## 4. Statistical Analysis

### 4.1 Logistic Regression
The primary model estimates the probability of adoption:
$$ \text{logit}(P(\text{Adoption}=1)) = \beta_0 + \beta_1(\text{Engagement}) + \sum \beta_i(\text{Covariates}) $$

- **Multicollinearity**: Variance Inflation Factor (VIF) is calculated for all predictors.
 VIF ≥ 5 is flagged as a collinearity warning. PCA is explicitly avoided per project constraints.
- **Multiple Testing**: Benjamini-Hochberg False Discovery Rate (FDR) correction (q ≤ 0.10)
 is applied to hypothesis tests.

### 4.2 Model Performance
- **ROC Curve**: Plotted to visualize trade-offs.
- **AUC**: Area Under the Curve is calculated and reported.

### 4.3 Mediation Analysis
Mediation effects are tested using the Baron & Kenny approach with bootstrap confidence intervals
(≥1000 resamples). Sensitivity analysis is conducted using E-values and Rosenbaum bounds
(gamma range including 2.5) to assess robustness to unobserved confounding. Results are
interpreted as "exploratory" due to the observational nature of the data.

## 5. Limitations

- **Power Analysis**: If the ratio of effective events to predictors is < 10, a shortfall is
 logged in `modeling_log.yaml` but execution continues.
- **Data Availability**: Reliance on synthetic data when real APIs are unreachable is
 documented as a limitation in `data/metadata.yaml`.
- **Causality**: As a cross-sectional study, causal inference is limited; mediation results
 are exploratory.

## 6. Reproducibility

- All random seeds are set via `code/config.py`.
- All modeling choices and logs are recorded in `modeling_log.yaml`.
- The pipeline is designed to run end-to-end via the `quickstart.md` script.