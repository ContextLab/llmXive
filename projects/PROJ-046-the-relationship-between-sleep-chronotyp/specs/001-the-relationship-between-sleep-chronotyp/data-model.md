# Data Model: The Relationship Between Sleep Chronotype and Moral Judgement

## Entity Definitions

### ParticipantRecord
Represents a single participant after ingestion and cleaning.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | Unique identifier | PK, Non-null |
| `meq_score` | float | Morningness-Eveningness Questionnaire score | Range [16, 86], Non-null for analysis |
| `chronotype` | enum | Derived label: "morning", "intermediate", "evening", "NA" | Derived from `meq_score` |
| `mfq_care` | float | Moral Foundations Care subscale score | Range [0, 100] |
| `mfq_fairness` | float | Moral Foundations Fairness subscale score | Range [0, 100] |
| `mfq_loyalty` | float | Moral Foundations Loyalty subscale score | Range [0, 100] |
| `mfq_authority` | float | Moral Foundations Authority subscale score | Range [0, 100] |
| `mfq_sanctity` | float | Moral Foundations Sanctity subscale score | Range [0, 100] |
| `psqi` | float | Pittsburgh Sleep Quality Index | Range [0, 21] |
| `acute_sleepiness` | float | Acute sleepiness rating (e.g., 0-10) | Non-null (FR-007) |
| `age` | integer | Age in years | > 18 |
| `sex` | string | Biological sex (e.g., "M", "F", "Other") | Categorical |
| `exclusion_reason` | string | Reason for exclusion if any (e.g., "missing_acute_sleepiness") | Nullable |

### AnalysisResult
Encapsulates the output of the statistical analysis.

| Field | Type | Description |
| :--- | :--- | :--- |
| `subscale` | string | Name of the MFQ subscale (e.g., "care") |
| `f_statistic` | float | F-statistic from ANCOVA |
| `p_value_raw` | float | Raw p-value |
| `p_value_adjusted` | float | Bonferroni-adjusted p-value |
| `significant` | boolean | Is `p_value_adjusted` < 0.01? |
| `effect_size_cohens_d` | float | Cohen's d for significant contrasts |
| `ci_lower` | float | Lower bound of 95% CI |
| `ci_upper` | float | Upper bound of 95% CI |

## Data Flow
1.  **Raw Ingestion**: Load a **single, pre-merged** CSV file containing all required columns (`MEQ_score`, `MFQ_*`, `PSQI`, `acute_sleepiness`, `age`, `sex`).
2.  **Validation**:
    *   Verify all required columns are present.
    *   **ABORT** if any required column is missing.
    *   Check ranges, flag missing `acute_sleepiness`.
    *   Calculate exclusion rate. **ABORT** if >20% of rows are unusable.
3.  **Classification**: Compute `chronotype`.
4.  **Filter**: Exclude rows with `chronotype == "NA"` or missing `acute_sleepiness`.
5.  **Analysis**: Run ANCOVA models.
6.  **Report**: Aggregate results into `AnalysisResult` table.

**Note**: The pipeline does **not** support merging disjoint datasets or simulating missing covariates. All data must be provided in a single merged file.