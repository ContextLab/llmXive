# Data Model: The Impact of Text Message Tone on Perceived Emotional Support

This document defines the canonical schemas for all core data artifacts used throughout the pipeline. All scripts validate inputs/outputs against these schemas (see `contracts/`).

## Primary Schemas (used by the pipeline)

- **Stimulus Schema** (`stimulus.schema.yaml`): defines the structure of `stimuli.csv`. This is the **single source of truth** for stimulus metadata.
- **Rating Schema** (`rating.schema.yaml`): defines the structure of `real_ratings.csv`. This is the **single source of truth** for participant rating data.

## Deprecated / Alias Schemas (retained for backward compatibility)

- `stimuli.schema.yaml` – **deprecated alias** of `stimulus.schema.yaml`. It is kept only to avoid breaking older commits; the pipeline does **not** validate against it.
- `ratings.schema.yaml` – **deprecated alias** of `rating.schema.yaml`. It is kept only for historical reasons; the pipeline validates against `rating.schema.yaml`.

The pipeline (and all plan references) uses the primary schemas above; deprecated schemas are documented solely for traceability.

## 1. Stimulus Schema (`stimulus.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `stimulus_id` | string | Unique identifier (`stim-XXXX`). |
| `base_scenario` | string | Text of the underlying situation (e.g., “I had a rough day”). |
| `emoji_count` | integer | Number of emojis in the message (0, 1, 2+ encoded as 2). |
| `punctuation_pattern` | string | `"standard"` or `"excessive"`. |
| `length_category` | string | `"short"` (< 10 words) or `"long"` (≥ 10 words). |
| `cue_intensity` | float | Weighted sum of the three cues (primary weighting). |
| `full_text` | string | The final generated message shown to participants. |

## 2. Rating Schema (`rating.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `participant_id` | string | Anonymized Prolific participant identifier. |
| `stimulus_id` | string | Foreign key to `stimulus_id`. |
| `relationship_type` | string | `"friend"` or `"acquaintance"` (randomized per trial). |
| `rating` | integer | 1‑7 Likert rating of perceived emotional support. |
| `timestamp` | string (ISO‑8601) | When the rating was submitted. |

## 3. Processed Analysis Ready Schema (`analysis_ready.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| All fields from **Stimulus Schema** | – | – |
| All fields from **Rating Schema** | – | – |
| `cue_intensity_weighting` | string | `"primary"`, `"equal"`, `"emoji_dominant"`, or `"punctuation_dominant"` (used in sensitivity runs). |

## 4. LMM Summary Schema (`lmm_summary.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `term` | string | Fixed‑effect name (e.g., `relationship[T.friend]:cue_intensity`). |
| `estimate` | float | Coefficient estimate (β). |
| `std_error` | float | Standard error. |
| `df` | float *(optional)* | Approximate degrees of freedom using Wald Z (normal approximation). |
| `t_value` | float | Wald Z‑based statistic. |
| `p_value` | float | Two‑tailed p‑value. |
| `ci_lower` | float | 95 % confidence interval lower bound. |
| `ci_upper` | float | 95 % confidence interval upper bound. |

All CSV files written by the pipeline must conform to the corresponding schema. Validation is performed by `tests/contract/` during CI.

## Schema Consolidation Note
- `stimulus.schema.yaml` and `rating.schema.yaml` are the **authoritative** schemas.
- `stimuli.schema.yaml` and `ratings.schema.yaml` are retained only as deprecated aliases; they should **not** be used by new code or validation steps.
- This consolidation eliminates ambiguity and satisfies the panel concerns about schema consistency.

## Entity Definitions

### Stimulus
A Stimulus represents a single text message scenario used in the experiment. It is generated programmatically by combining a base scenario with variations in emoji usage, punctuation, and length. Each stimulus is uniquely identified and carries metadata about its cue intensity.

### Participant
A Participant represents a human subject in the study. In this data model, participants are identified by an anonymized ID derived from their Prolific ID. The model tracks their ratings across different stimuli and relationship contexts but does not store personally identifiable information (PII) in the analysis datasets.

### Rating
A Rating is a single data point representing a participant's evaluation of a stimulus. It links a Participant to a Stimulus within a specific relationship context and records the perceived emotional support score.

### AnalysisResult
An AnalysisResult encapsulates the output of the statistical modeling phase. It aggregates the fixed effects, random effects variance components, and model fit statistics derived from the Linear Mixed Model (LMM) analysis, serving as the primary output for the research findings.
