# Data Model: The Relationship Between Personality Traits and Response to Personalized AI Feedback

## Entities

### Participant
An abstract entity representing a single row in the analysis dataset.
- **ID**: Unique integer or string (generated or from source).
- **Traits**: 5 continuous variables (0-50 scale).
- **Feedback**: Text and Label.
- **Responses**: 3 continuous variables (1-5 Likert scale).
- **Feedback Type**: Categorical variable (0=Corrective, 1=Positive).

### Feedback Scenario
A specific instance of AI text and its classification label.
- **Text**: String (the AI feedback).
- **Label**: Integer (0 or 1, mapped to feedback type).

## Schema Definition

### Raw Data Schema (Source: `ai-generated-text-classification`)
| Column | Type | Description |
| :--- | :--- | :--- |
| `text` | string | The AI-generated feedback text. |
| `label` | integer | Classification label (0/1). |

### Derived Data Schema (`analysis_data.csv`)
| Column | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `participant_id` | int | Unique identifier. | Generated |
| `openness` | float | Openness score (0-50). | Synthetic (Theoretical) |
| `conscientiousness` | float | Conscientiousness score (0-50). | Synthetic (Theoretical) |
| `extraversion` | float | Extraversion score (0-50). | Synthetic (Theoretical) |
| `agreeableness` | float | Agreeableness score (0-50). | Synthetic (Theoretical) |
| `neuroticism` | float | Neuroticism score (0-50). | Synthetic (Theoretical) |
| `receptivity_score` | float | Receptivity (1-5). | Theoretical Simulation |
| `anxiety_level` | float | Anxiety (1-5). | Theoretical Simulation |
| `behavioral_intention` | float | Intention (1-5). | Theoretical Simulation |
| `feedback_text` | string | Original feedback text. | Source |
| `feedback_label` | int | Original classification. | Source |
| `feedback_type` | int | Feedback type (0=Corrective, 1=Positive). | Derived from `label` |

## Data Flow

1.  **Download**: `raw/ai_generated.parquet` → `raw/ai_generated.csv`
2.  **Synthesize**: Generate `openness`...`neuroticism` columns (Mean=30, SD=8).
3.  **Map**: `label` → `feedback_type` (0=Corrective, 1=Positive).
4.  **Simulate**: Generate `receptivity_score`, `anxiety_level`, `behavioral_intention` based on a *theoretical model* (e.g., `receptivity_score` = f(Openness, Neuroticism) + noise).
5.  **Merge**: Combine into `data/processed/analysis_data.csv`.
6.  **Validate**: Check N ≥ 50, check nulls < 10%.
