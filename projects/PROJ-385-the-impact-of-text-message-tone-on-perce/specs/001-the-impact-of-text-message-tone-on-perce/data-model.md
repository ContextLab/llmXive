# Data Model: The Impact of Text Message Tone on Perceived Emotional Support

## 1. Overview

This document defines the data structures used in the project. All data is stored in CSV format for maximum portability and compatibility with statistical tools. The model enforces a strict separation between **Stimulus Features** (independent variables) and **Ratings** (dependent variables).

**Data Source Hierarchy**:
- `data/raw/real_ratings.csv`: **Single Source of Truth** for empirical findings.
- `data/raw/simulated_ratings.csv`: **Validation Only**. Results derived from this file are never reported as findings.

## 2. Data Entities

### 2.1 Stimulus (`data/raw/stimuli.csv`)
Represents the generated text message variants.

| Column Name | Type | Description | Constraints |
|-------------|------|-------------|-------------|
| `stimulus_id` | String | Unique identifier for the stimulus. | PK, Format: `S{N}` |
| `base_scenario` | String | The underlying situation (e.g., "I had a rough day"). | Not null |
| `emoji_count` | Integer | Number of emojis used (0, 1, 2+). | 0, 1, 2 |
| `punctuation_pattern` | String | Pattern type (e.g., "standard", "exaggerated"). | Enum |
| `length_category` | String | Length bucket (e.g., "short", "long"). | Enum |
| `cue_intensity_score` | Float | Calculated weighted score of cues. | Computed |
| `text_content` | String | The full generated text message. | Not null |

### 2.2 Rating (`data/raw/real_ratings.csv`, `data/raw/simulated_ratings.csv`)
Represents the human (or simulated) rating of a stimulus in a specific context.

| Column Name | Type | Description | Constraints |
|-------------|------|-------------|-------------|
| `rating_id` | String | Unique identifier for the rating record. | PK, Format: `R{N}` |
| `participant_id` | String | Unique ID for the participant (hashed Prolific ID for real data). | Not null |
| `stimulus_id` | String | Foreign key to `stimuli.stimulus_id`. | FK |
| `relationship_context` | String | Context of the sender (friend/acquaintance). | Enum: "friend", "acquaintance" |
| `support_rating` | Integer | Perceived emotional support (1-7 Likert). | 1 ≤ x ≤ 7 |
| `timestamp` | ISO8601 | Time of rating. | Optional |
| `is_straight_lined` | Boolean | Flag for data quality check. | Default: False |

### 2.3 Power Analysis (`data/processed/power_analysis_results.json`)
Output of the power analysis step.

| Field | Type | Description |
|-------|------|-------------|
| `target_N` | Integer | Required number of participants. |
| `effect_size_f2` | Float | Assumed effect size from literature. |
| `power` | Float | Target power (e.g., 0.80). |
| `alpha` | Float | Significance level (e.g., 0.05). |
| `method` | String | Method used (e.g., "simulation", "F-test"). |

### 2.4 Analysis Results (`data/processed/lmm_results.json`)
Output of the statistical model.

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | String | Unique run ID. |
| `fixed_effects` | Object | Dictionary of coefficient estimates (including quadratic term). |
| `random_effects` | Object | Variance components for random intercepts. |
| `interaction_p_value` | Float | P-value for the interaction term. |
| `interaction_effect_size` | Float | Cohen's f² or partial R². |
| `post_hoc_comparisons` | Array | List of pairwise comparisons with adjusted p-values. |
| `sensitivity_report` | Object | Results of the robustness checks. |
| `exclusion_summary` | Object | Summary of excluded participants (straight-lining). |

## 3. Data Flow

1.  **Generation**: `01_generate_stimuli.py` → `data/raw/stimuli.csv`
2.  **Power Analysis**: `01_power_analysis.py` (reads `stimuli.csv`) → `data/processed/power_analysis_results.json`
3.  **Simulation**: `02_simulate_ratings.py` (reads `stimuli.csv`, `power_analysis_results.json`) → `data/raw/simulated_ratings.csv` (Validation Only)
4.  **Real Collection**: `04_collect_real_data.py` (reads `stimuli.csv`, `power_analysis_results.json`) → `data/raw/real_ratings.csv` (SSoT)
5.  **Analysis**: `03_lmm_analysis.py` (reads `stimuli.csv`, `real_ratings.csv`) → `data/processed/lmm_results.json`
6.  **Sensitivity**: `04_sensitivity_analysis.py` (reads `lmm_results.json`) → `data/processed/sensitivity_report.json`

## 4. Data Quality Rules

- **Uniqueness**: `stimulus_id` and `rating_id` must be unique.
- **Referential Integrity**: Every `rating.stimulus_id` must exist in `stimuli`.
- **Range Checks**: `support_rating` must be between 1 and 7.
- **Straight-lining**: If `variance(support_rating)` for a `participant_id` is 0, `is_straight_lined` is set to True.
- **Source Hierarchy**: Analysis must prioritize `real_ratings.csv` if it exists; otherwise, fall back to `simulated_ratings.csv` for CI validation only.