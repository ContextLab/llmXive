# Data Model: The Influence of Simulated Social Status on Risk-Taking Behavior

## Overview
This document defines the data structures, schemas, and relationships for the project. The data model supports a **Between-Subjects** randomized experimental design where each participant is exposed to exactly one simulated social status cue and observed behavior, then performs a risk-taking task.

## Entities

### Participant
An individual unit of observation.
- **Attributes**:
  - `participant_id`: Unique string identifier (UUID).
  - `condition_id`: Identifier for the experimental condition (High/Low Status × Risky/Conservative Behavior).
  - `risk_taking_score`: Numeric value representing the outcome.
  - `status_level`: Categorical (High, Low).
  - `observed_behavior`: Categorical (Risky, Conservative).
- **Constraint**: **One row per participant**. No repeated measures.

### Condition
A combination of experimental factors.
- **Combinations**:
  1. High Status / Risky Behavior
  2. High Status / Conservative Behavior
  3. Low Status / Risky Behavior
  4. Low Status / Conservative Behavior

## Data Flow

1.  **Generation**: `code/generate_data.py` creates a synthetic dataset.
    - Inputs: Random seed, effect size parameters (fixed in `research.md`).
    - Output: `data/raw/synthetic_data.csv`.
2.  **Preprocessing**: `code/preprocess.py` cleans and transforms data.
    - Inputs: `data/raw/synthetic_data.csv`.
    - Operations:
      - Map raw scores to categorical factors (FR-002).
      - Handle missing values (imputation or exclusion).
      - Verify no variance in predictors (edge case handling).
    - Output: `data/processed/cleaned_data.csv`.
3.  **Analysis**: `code/analysis.py` fits models.
    - Inputs: `data/processed/cleaned_data.csv`.
    - Output: `data/results/model_summary.json`, `data/results/sensitivity_analysis.csv`.
4.  **Reporting**: `code/report.py` generates plots.
    - Inputs: Model results.
    - Output: `data/results/forest_plot.png`, `data/results/report.html`.

## Schema Definitions

### Raw Data Schema (`synthetic_data.csv`)
| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `participant_id` | string | Unique ID | Non-null, unique |
| `status_level` | string | Experimental status cue | Values: "High", "Low" |
| `observed_behavior` | string | Observed agent behavior | Values: "Risky", "Conservative" |
| `risk_taking_score` | float | Outcome measure | Non-null, > 0 |
| `trial_id` | string | Optional trial identifier | Nullable |

### Processed Data Schema (`cleaned_data.csv`)
| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `participant_id` | string | Unique ID | Non-null, unique |
| `status_level` | category | Categorical factor | Levels: High, Low |
| `observed_behavior` | category | Categorical factor | Levels: Risky, Conservative |
| `risk_taking_score` | float | Cleaned outcome | Non-null |
| `is_outlier` | boolean | Flagged by sensitivity analysis | Default: False |

## Data Constraints & Validation

- **Missing Values**:
  - If `risk_taking_score` > 10% missing: Apply imputation strategy or exclude (FR-001).
  - If `status_level` or `observed_behavior` missing: Exclude row.
- **Variance Check**:
  - If `status_level` has only one unique value: Halt with error (Edge Case).
  - If `observed_behavior` has only one unique value: Halt with error (Edge Case).
- **Data Type Switch**:
  - If `risk_taking_score` is binary (0/1): Use `binomial` family.
  - If `risk_taking_score` is continuous: Use `gaussian` family (Linear Model).

## Storage & Hygiene

- **Raw Data**: Stored in `data/raw/`. Checksum recorded in `data/checksums.json`.
- **Processed Data**: Stored in `data/processed/`. No in-place modifications.
- **PII**: No real PII generated. `participant_id` is a random UUID.
- **Versioning**: Every data file has a content hash. Changes update `state/` timestamps.

## Assumptions
- **Measurement Validity**: The synthetic `risk_taking_score` mimics the distribution of validated instruments (e.g., BART) as per **Assumption about measurement validity**.
- **Orthogonality**: `status_level` and `observed_behavior` are generated independently to ensure no collinearity before model fitting.
- **Design**: Between-Subjects design (one observation per participant) is used to avoid singular fit issues in linear modeling.