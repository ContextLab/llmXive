# Data Model: The Impact of Perceived Social Support on Resilience to Online Harassment

## Dataset Scope
This project utilizes a **single-dataset** design. All analysis is performed on the **Cyberbullying Survey 2021**.

## Excluded Datasets
### General Social Survey (GSS) 2022
The GSS 2022 dataset is **excluded** from the data model and analysis pipeline.

**Reasons for Exclusion:**
1. **Confounding with Dataset Source**: In a combined dataset, the variable `harassment_exposure` would be perfectly correlated with the source dataset (GSS vs. Cyberbullying Survey). This creates a non-identifiable model where the interaction term between social support and harassment cannot be estimated without the "Dataset Source" variable acting as a perfect confounder.
2. **Missing Outcome Measures**: The GSS 2022 lacks the specific item set required to compute the PCL-5 (PTSD) scale, a primary outcome of interest.
3. **Construct Validity**: The definitions of "Social Support" and "Online Harassment" in the GSS are not directly comparable to those in the Cyberbullying Survey 2021, preventing valid harmonization.

## Data Dictionary (Cyberbullying Survey 2021)

### Demographics
- `age`: Continuous, years.
- `gender`: Categorical (Male, Female, Non-binary, Other).
- `education`: Ordinal (High School, Some College, Bachelor's, Graduate).
- `income`: Continuous, annual household income.

### Predictors
- `social_support_items`: Raw items for the Perceived Social Support Scale (PSSS).
- `harassment_severity_items`: Raw items measuring frequency and severity of online harassment.
- `harassment_exposure`: Binary derived variable (1 if `harassment_severity` > 0, else 0).
- `harassment_severity`: Continuous derived score.
- `platform`: Categorical (Social Media, Gaming, Forums, Other).

### Outcomes
- `depression_items`: Raw items for CES-D scale.
- `anxiety_items`: Raw items for GAD-7 scale.
- `ptsd_items`: Raw items for PCL-5 scale.

### Derived Scores
- `depression_score`: Sum of CES-D items (0-60).
- `anxiety_score`: Sum of GAD-7 items (0-21).
- `ptsd_score`: Sum of PCL-5 items (0-80).

## Data Flow
1. **Ingestion**: Load raw Cyberbullying Survey 2021 data.
2. **Preprocessing**: Handle missingness (MICE), score scales.
3. **Cohort Construction**: Filter invalid scores, derive `harassment_exposure`.
4. **Validation**: Check variance and multicollinearity.
5. **Analysis**: Fit OLS models with interaction terms.