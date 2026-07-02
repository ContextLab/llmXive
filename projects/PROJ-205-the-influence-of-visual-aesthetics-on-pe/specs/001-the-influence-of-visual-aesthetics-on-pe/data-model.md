# Data Model: The Influence of Visual Aesthetics on Perceived Credibility of Online Information

## 1. Entity Relationship Overview

The data model consists of three primary entities: `Participant`, `Stimulus`, and `Response`.

-   **Participant**: The human subject. Anonymized ID, demographics.
-   **Stimulus**: One of the 4 visual conditions.
-   **Response**: The rating given by a participant to a specific stimulus.

**Cardinality**:
-   One Participant submits 4 Responses (one per Stimulus).
-   One Stimulus condition is rated by N Participants.

## 2. Data Schema Definitions

### 2.1 Raw Data Schema (Survey Output)
*File: `data/raw/participants.csv`*

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `participant_id` | String | Unique anonymized ID (UUID) | PK, Non-null |
| `timestamp_start` | ISO8601 | Survey start time | Non-null |
| `timestamp_end` | ISO8601 | Survey end time | Non-null |
| `consent_given` | Boolean | IRB Consent status | Must be True |
| `order_sequence` | Integer | Latin Square sequence (1-4) | 1, 2, 3, or 4 |
| `stimulus_1` | String | Condition name for 1st stimulus | Enum |
| `credibility_1` | Integer | Rating 1-7 | 1..7 |
| `professionalism_1`| Integer | Rating 1-7 | 1..7 |
| `stimulus_2` | String | Condition name for 2nd stimulus | Enum |
| `credibility_2` | Integer | Rating 1-7 | 1..7 |
| `professionalism_2`| Integer | Rating 1-7 | 1..7 |
| `stimulus_3` | String | Condition name for 3rd stimulus | Enum |
| `credibility_3` | Integer | Rating 1-7 | 1..7 |
| `professionalism_3`| Integer | Rating 1-7 | 1..7 |
| `stimulus_4` | String | Condition name for 4th stimulus | Enum |
| `credibility_4` | Integer | Rating 1-7 | 1..7 |
| `professionalism_4`| Integer | Rating 1-7 | 1..7 |
| `age` | Integer | Age in years | 18..100 |
| `education` | String | Education level | Enum: "HS", "Bachelor", "Master", "PhD" |
| `ip_hash` | String | Hashed IP for deduplication | Non-null, PII-stripped |
| `device_info` | String | User Agent string | Non-null |
| `text_version` | String | Hash of `code/stimuli/text_content.txt` | Non-null, ensures text constancy |

### 2.2 Processed Data Schema (Analysis Input)
*File: `data/processed/analysis_ready.csv`*
*Long format for ANOVA/LMM*

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `participant_id` | String | FK to Participant |
| `condition` | String | Stimulus Condition (Professional, Minimalist, etc.) |
| `credibility_score` | Integer | 1-7 |
| `professionalism_score`| Integer | 1-7 |
| `age` | Integer | Continuous |
| `education` | String | Ordinal Categorical |

## 3. Data Integrity Rules

1.  **Completeness**: A participant record is invalid if any of the 8 rating fields (4 credibility + 4 professionalism) are missing. (FR-008).
2.  **Range Check**: All Likert ratings must be integers between 1 and 7.
3.  **Deduplication**: Records with identical `ip_hash` within a 24-hour window are flagged and excluded (Edge Case handling).
4.  **Consent**: No record is processed if `consent_given` is False.
5.  **PII Stripping**: `ip_hash` is a one-way hash. No raw IPs stored.
6.  **Text Consistency**: The `text_version` hash must match the hash of `code/stimuli/text_content.txt` to ensure the textual content was constant across all stimuli.