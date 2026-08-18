# Data Model Specification

## Entities

### Stimulus
| Field | Type | Description |
|-------|------|-------------|
| stimulus_id | String | Unique identifier (e.g., "prof_01") |
| type | Enum | 'professional', 'minimalist', 'low_quality', 'neutral' |
| content | Text | The HTML content of the stimulus |

### Response
| Field | Type | Description |
|-------|------|-------------|
| response_id | String | Unique identifier |
| participant_id | String | Anonymized participant ID |
| stimulus_id | String | Reference to Stimulus |
| credibility_rating | Integer | 1-7 Likert scale |
| professionalism_rating | Integer | 1-7 Likert scale |
| timestamp | DateTime | When the rating was submitted |

### Participant
| Field | Type | Description |
|-------|------|-------------|
| participant_id | String | Unique ID |
| age | Integer | Age in years |
| education_level | Integer | 1=High School, 2=Bachelor's, 3=Master's, 4=PhD |
| hashed_ip | String | SHA-256 hash of IP address |
| consent_given | Boolean | Whether consent was accepted |
| consent_timestamp | DateTime | When consent was given |

## Relationships
- One Participant has many Responses (4 per participant in this study).
- One Stimulus can be rated by many Participants.

## CSV Schema (Raw Data)
| Column | Type | Constraints |
|--------|------|-------------|
| participant_id | String | Not Null |
| stimulus_type | String | Enum |
| credibility | Integer | 1-7 |
| professionalism | Integer | 1-7 |
| age | Integer | 18-99 |
| education | Integer | 1-4 |
| hashed_ip | String | SHA-256 |
| timestamp | DateTime | ISO 8601 |
| submission_status | String | 'complete', 'partial', 'timeout' |
| user_agent | String | Truncated |
