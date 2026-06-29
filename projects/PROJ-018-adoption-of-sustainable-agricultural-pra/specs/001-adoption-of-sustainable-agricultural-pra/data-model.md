# Data Model: Adoption of Sustainable Agricultural Practices in Low‑Income Areas through Community Engagement

## Entities & Attributes

### SurveyRecord
Represents a single farmer's survey response.
- `id`: String (Unique Identifier)
- `country_code`: String (ISO 3166-1 alpha-3)
- `age`: Integer (Years)
- `education_level`: String (Categorical: None, Primary, Secondary, Tertiary)
- `farm_size_ha`: Float (Hectares)
- `credit_access`: Boolean (1 = Access, 0 = No Access)
- `practice_adoption_flags`: List[String] (e.g., ["agroforestry", "organic_inputs", "water_conservation"])
- `engagement_item_1`: Float (Membership in farmer group)
- `engagement_item_2`: Float (Participation in extension)
- `engagement_item_3`: Float (Collective action participation)
- `engagement_item_4`: Float (Frequency of knowledge exchange)

### Derived Variables
- `engagement_score`: Float (0–100, Composite Index)
- `adoption_binary`: Integer (0 or 1)
- `vif_scores`: Map[String, Float] (Variance Inflation Factors)
- `correlation_matrix`: Map[String, Map[String, Float]] (Pairwise correlations for collinearity assessment)
- `efa_loadings`: Map[String, Map[String, Float]] (Factor loadings from exploratory factor analysis)
- `convergent_validity`: Map[String, Float] (Correlations with theoretically related constructs)
- `model_coef`: Map[String, Float] (Regression Coefficients)
- `mediation_sensitivity`: Map[String, Float] (E-values, Rosenbaum bounds for mediation robustness)

## Data Flow

1.  **Raw Input**: `data/raw/survey_data.csv` (or synthetic equivalent).
2.  **Cleaned Input**: `data/processed/cleaned_survey_data.csv` (Missing values imputed/removed).
3.  **Engineered Input**: `data/processed/engineered_survey_data.csv` (Includes `engagement_score`, `adoption_binary`, validity metrics).
4.  **Model Output**: `results/model_results.json` (Coefficients, AUC, VIF, correlation matrix, EFA loadings, mediation sensitivity).
5.  **Report Output**: `results/final_report.pdf`.

## Constraints & Validations

- **Missing Data**: Records with > 30% missing values in required fields are excluded.
- **Engagement Score**: Calculated only if ≥ 3 proxy items available. If < 3, flag limitation. **All 4 engagement items required per contracts/dataset.schema.yaml**.
- **Adoption Binary**: 1 if `len(practice_adoption_flags) >= 1`.
- **VIF**: Flag if ≥ 5. **Correlation matrix computed; pairwise correlations > 0.70 flagged**.
- **FDR**: Adjusted p-values required for all tests.
- **EFA**: Factor loadings reported for construct validity assessment.
- **Sensitivity**: E-values and Rosenbaum bounds computed for mediation robustness.

## Schema Contracts

See `contracts/dataset.schema.yaml` for input validation (requires all 4 engagement items).
See `contracts/results.schema.yaml` for output validation.