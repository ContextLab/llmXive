# Data Model: The Impact of Perspective-Taking on Moral Outrage in Online Discourse

## Overview
This document defines the data structures for the stimulus curation, participant response processing, and analysis output. All data is stored in `data/` and processed in `code/`.

## Entity Definitions

### 1. Stimulus
Represents a single Twitter post paired with an experimental instruction.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `stimulus_id` | string | Unique identifier (e.g., `S-001`) | PK |
| `post_text` | string | The original Twitter post text | Not Null |
| `topic` | string | Topic category (e.g., `climate`, `immigration`) | Enum |
| `vader_sentiment` | float | Automated sentiment score (-1.0 to 1.0) | Nullable (computed if missing) |
| `intensity_bin` | string | `moderate` or `high` | Derived from `vader_sentiment` |
| `instruction_type` | string | `perspective_taking` or `control` | Enum |
| `instruction_text` | string | The full prompt text | Not Null |

### 2. Participant
Represents an experimental subject and their aggregated responses.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | string | Unique identifier (e.g., `P-001`) | PK |
| `condition` | string | `perspective_taking` or `control` | Not Null |
| `consent_given` | boolean | True if participant provided informed consent | Required, Default: False |
| `attention_check_failures` | int | Number of failed attention checks | ≥ 0 |
| `is_straight_liner` | boolean | True if zero variance in scale items | Calculated |
| `is_valid` | boolean | True if passed attention, not straight-liner, and consent given | Derived |
| `mean_outrage_score` | float | Average of 7-item Moral Outrage Scale | Calculated |
| `n_posts_viewed` | int | Number of posts rated by participant | ≥ 0 |

### 3. AnalysisResult
Represents the statistical output of the study.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `test_type` | string | `t_test` or `mixed_effects` | Enum |
| `statistic` | float | t-statistic or t-statistic from LME | Not Null |
| `p_value` | float | Significance level | [0, 1] |
| `effect_size` | float | Cohen's d (for t-test) or Coefficient (for LME) | Nullable |
| `ci_lower` | float | Lower bound of 95% CI | Nullable |
| `ci_upper` | float | Upper bound of 95% CI | Nullable |
| `n_group_a` | int | Count in perspective-taking group | ≥ 0 |
| `n_group_b` | int | Count in control group | ≥ 0 |
| `icc_value` | float | Intra-class correlation (repeated measures) | [0, 1] |
| `analysis_path` | string | `t_test` or `mixed_effects_fallback` | Enum |

## File Formats

- **Raw Stimuli**: `data/raw/twitter_posts.parquet`
- **Processed Stimuli**: `data/processed/stimuli.json` (List of Stimulus objects)
- **Raw Participants**: `data/raw/participant_responses.csv`
- **Cleaned Participants**: `data/processed/cleaned_participants.csv` (List of Participant objects)
- **Analysis Output**: `data/processed/analysis_results.json` (List of AnalysisResult objects)