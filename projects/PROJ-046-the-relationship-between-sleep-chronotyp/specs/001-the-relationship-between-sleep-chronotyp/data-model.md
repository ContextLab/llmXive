# Data Model: The Relationship Between Sleep Chronotype and Moral Judgement

## Entity: ParticipantRecord

Represents a single respondent in the study.

### Attributes

| Attribute | Type | Description | Constraints | Source/Validation |
|-----------|------|-------------|-------------|-------------------|
| `participant_id` | string | Unique identifier | Not NULL, Unique | Generated |
| `MEQ_score` | integer | Morningness-Eveningness Questionnaire score | Range [16, 86], Not NULL | MEQ (Horne & Östberg) |
| `chronotype` | enum | Derived label: "morning", "intermediate", "evening", "NA" | Derived from MEQ_score | Rule: ≥59→morning, ≤41→evening |
| `MFQ_care` | float | Moral Foundations: Care subscale score | Range [0, 40] | MFQ (Graham et al.) |
| `MFQ_fairness` | float | Moral Foundations: Fairness subscale score | Range [0, 40] | MFQ |
| `MFQ_loyalty` | float | Moral Foundations: Loyalty subscale score | Range [0, 40] | MFQ |
| `MFQ_authority` | float | Moral Foundations: Authority subscale score | Range [0, 40] | MFQ |
| `MFQ_sanctity` | float | Moral Foundations: Sanctity subscale score | Range [0, 40] | MFQ |
| `PSQI` | float | Pittsburgh Sleep Quality Index | Range [0, 21] | PSQI (Buysse et al.) |
| `acute_sleepiness` | float | Acute sleepiness score (e.g., 1-10) | Range [0, 10] | Self-report/Actigraphy |
| `age` | integer | Age in years | > 0 | Demographics |
| `sex` | enum | "male", "female", "other" | Not NULL | Demographics |
| `exclusion_reason` | string | Reason for exclusion if any | NULL if included | Validation logic |

## Entity: AnalysisResult

Encapsulates the output of the statistical analysis.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `subscale` | string | MFQ subscale name (e.g., "care") |
| `f_statistic` | float | ANCOVA F-statistic |
| `p_value` | float | Raw p-value |
| `p_value_adj` | float | Bonferroni-adjusted p-value |
| `significant` | boolean | Is p_value_adj < 0.01? |
| `cohen_d` | float | Effect size for significant contrasts |
| `ci_lower` | float | Lower bound of 95% CI for Cohen's d |
| `ci_upper` | float | Upper bound of 95% CI for Cohen's d |
| `vif` | float | Variance Inflation Factor for predictors |

## Data Flow

1. **Ingest**: Raw CSV -> `ParticipantRecord` (with validation).
2. **Classify**: `MEQ_score` -> `chronotype` label.
3. **Filter**: Remove rows with `chronotype = NA` or missing covariates.
4. **Analyze**: Filtered data -> `AnalysisResult` per subscale.
5. **Report**: Aggregate `AnalysisResult` -> Final Report.
