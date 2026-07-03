# Data Model: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

## 1. Overview

This document defines the data structures used throughout the project. All data is stored in JSON or CSV format within the `data/` directory. The model supports both **Simulated** and **Human** participant streams, ensuring data separation (FR-009).

## 2. Core Entities

### 2.1 Stimulus
A single social media post with metadata and instruction variants.

- **`post_id`**: Unique identifier (string).
- **`text`**: The content of the social media post (string).
- **`topic`**: The controversial topic (e.g., "climate", "immigration") (string).
- **`outrage_label`**: The original label from the dataset (e.g., "high") (string).
- **`instructions`**: A dictionary containing the two instruction variants.
  - **`perspective_taking`**: The prompt text for the PT condition (string).
  - **`control`**: The prompt text for the control condition (string).

### 2.2 Participant
A record of a subject (simulated or human) who completed the experiment.

- **`participant_id`**: Unique identifier (string).
- **`type`**: "simulated" or "human" (string).
- **`condition`**: "perspective_taking" or "control" (string).
- **`attention_checks`**: A list of booleans indicating pass/fail for each embedded check.
- **`attention_checks_passed`**: Boolean (True if ≤2 missed checks, derived from `attention_checks`).
- **`demographics`**: Optional dictionary (age, gender, etc.) for human data.
- **`responses`**: A list of integers (1-7) representing the Moral Outrage Scale items.
- **`mean_outrage`**: The calculated mean of the responses (float).

### 2.3 Analysis Result
The output of the statistical analysis.

- **`test_type`**: "lmm" or "mann_whitney" (string).
- **`fixed_effects`**: Dictionary of coefficients and p-values for fixed effects.
- **`random_effects`**: Variance components for random effects.
- **`ci_lower`, `ci_upper`**: % Confidence Interval bounds (float).
- **`sample_sizes`**: Dictionary with `n_pt` and `n_control`.

## 3. File Structure

```text
data/
├── raw/
│   └── against_the_others_raw.json    # Original dataset (checksummed)
├── processed/
│   ├── stimuli.json                   # Filtered & curated a set of stimuli

The research question, method, and references remain as originally planned, with the specific count generalized to a qualitative description.
│   ├── simulation_results.csv         # Synthetic participant data
│   └── human_results.csv              # Human participant data (future)
└── analysis/
    └── stats_report.json              # Final statistical outputs
```

## 4. Data Flow

1. **Ingestion**: `raw/` → `processed/stimuli.json` (Filtering, Sampling).
2. **Simulation**: `stimuli.json` + `random_seed` → `simulation_results.csv` (Assignment, Scoring).
3. **Analysis**: `simulation_results.csv` → `stats_report.json` (LMM, U-test).
4. **Human**: `human_results.csv` (same schema as simulation) → `stats_report.json`.

## 5. Constraints & Validation

- **Stimuli**: Must have entries (multiple per topic).
- **Responses**: Must be integers between 1 and 7.
- **Attention Checks**: `attention_checks` must be a list of 5 booleans. `attention_checks_passed` is derived as `sum(attention_checks) >= 3`.
- **Separation**: `type` field must strictly distinguish "simulated" vs "human".