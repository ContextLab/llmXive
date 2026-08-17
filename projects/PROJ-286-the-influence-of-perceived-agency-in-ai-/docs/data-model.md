# Data Model: The Influence of Perceived Agency in AI Interactions on Trust

This document describes the core data entities, their attributes, and their relationships for the research project. It serves as the canonical reference for data collection, processing, and analysis pipelines.

All data artifacts must conform to the schemas defined in `specs/001-perceived-agency-trust/contracts/`.

## 1. Overview

The project data model follows a standard experimental design structure:
1. **Participants**: Individual human subjects who complete the experiment.
2. **Conditions**: The experimental groups (High Agency, Low Agency, Control) assigned to participants.
3. **Results**: The aggregated outcomes derived from participant responses, including trust scores, adherence rates, and statistical test results.

## 2. Entity Definitions

### 2.1 Participant

The `Participant` entity represents a single user session in the experiment. It captures demographic metadata (if any), the assigned experimental condition, behavioral metrics, and psychometric survey responses.

**Source File**: `data/raw/participant_*.csv`
**Contract Reference**: `specs/001-perceived-agency-trust/contracts/participant.schema.yaml`

**Attributes**:
| Field Name | Type | Description | Constraints |
|:--- |:--- |:--- |:--- |
| `participant_id` | UUID | Unique identifier for the participant. | Generated at session start; immutable. |
| `condition` | Enum | The experimental condition assigned. | Values: `High`, `Low`, `Control`. |
| `adherence_rate` | Float | Percentage of AI recommendations followed. | Range: 0.0 to 100.0. |
| `trust_score` | Float | Mean score of the 12-item trust scale. | Range: 1.0 to 5.0. |
| `attention_check_status` | Boolean | Pass/fail status of attention checks. | `True` if passed, `False` otherwise. |
| `trust_item_1`... `trust_item_12` | Integer | Individual responses to Lee & See (2004) scale items. | Range: 1 (Strongly Disagree) to 5 (Strongly Agree). |
| `perceived_agency_score` | Integer | Manipulation check score (1-7 Likert). | Range: 1 to 7. |
| `session_timestamp` | ISO8601 | Time of data export. | Format: `YYYY-MM-DDTHH:MM:SS`. |

### 2.2 Condition

The `Condition` entity is a categorical variable representing the independent variable manipulation. While not stored as a separate table, it defines the grouping logic for analysis.

**Levels**:
1. **High**: Participants interact with functional sliders that *appear* to control the AI but do not alter the underlying algorithmic output.
2. **Low**: Participants have restricted or non-functional controls, simulating low agency.
3. **Control**: Participants view a static AI display with no interactive elements.

**Relationship**: One-to-Many (One Condition level is assigned to Many Participants).

### 2.3 Result

The `Result` entity encompasses the statistical outputs derived from aggregating participant data. These are typically stored in JSON or CSV formats for reporting.

**Source File**: `data/processed/analysis_results.json`, `docs/report.md`
**Contract Reference**: `specs/001-perceived-agency-trust/contracts/analysis_output.schema.yaml`

**Attributes**:
| Field Name | Type | Description |
|:--- |:--- |:--- |
| `anova_summary` | Object | F-statistic, p-value, and degrees of freedom for the One-Way ANOVA. |
| `planned_contrasts` | List[Object] | Results for High vs. Low and (High+Low) vs. Control comparisons. |
| `post_hoc_tests` | List[Object] | Tukey HSD pairwise comparisons with family-wise error rate adjustment. |
| `effect_sizes` | List[Object] | Cohen's d values for all pairwise comparisons. |
| `power_analysis` | Object | Pre-study and achieved power metrics. |
| `sensitivity_analysis` | List[Object] | Results from threshold sweeps (exclusion criteria). |

## 3. Relationships

```mermaid
erDiagram
 PARTICIPANT ||--o{ RESULT: "contributes to"
 CONDITION ||--|{ PARTICIPANT: "assigns"

 PARTICIPANT {
 UUID participant_id PK
 Enum condition FK
 Float adherence_rate
 Float trust_score
 Boolean attention_check_status
 Integer trust_item_1..12
 Integer perceived_agency_score
 }

 CONDITION {
 Enum level PK
 Description description
 }

 RESULT {
 String result_id PK
 JSON anova_summary
 JSON planned_contrasts
 JSON post_hoc_tests
 JSON effect_sizes
 }
```

## 4. Data Flow

1. **Ingestion**: The `code/experiment/app.py` collects raw data from users and exports it to `data/raw/` as CSV files matching `participant.schema.yaml`.
2. **Validation**: `code/analysis/data_cleaning.py` reads raw CSVs, validates against the schema, handles missing values, and writes cleaned data to `data/processed/`.
3. **Analysis**: `code/analysis/run_analysis.py` loads cleaned data, computes statistics (ANOVA, contrasts, etc.), and generates `analysis_output` artifacts.
4. **Reporting**: `code/analysis/report.py` synthesizes the analysis artifacts and pre-study power data into the final `docs/report.md`.

## 5. Compliance

- **Schema Enforcement**: All data export scripts must validate data against `specs/001-perceived-agency-trust/contracts/participant.schema.yaml` before writing to disk.
- **PII Protection**: No personally identifiable information (PII) is stored. `participant_id` is a UUID.
- **Reproducibility**: All analysis scripts must use the `seed` defined in `code/experiment/config.yaml` to ensure deterministic randomization and bootstrapping.