# Data Model: Visual Detail and False Memory Susceptibility

## Entities

### Image (Stimulus)
Represents a visual stimulus used in the experiment.
*   `image_id`: Unique identifier (UUID).
*   `baseline_path`: Path to the original image.
*   `enhanced_path`: Path to the image with added detail.
*   `reduced_path`: Path to the image with removed detail.
*   `complexity_score`: Float (0.0-1.0) derived from metadata or calculated (edge density, texture entropy).
*   `manipulation_params`: JSON object (e.g., `{"objects_added": 3, "blur_radius": 5, "semantic_relationship": "cup_on_table"}`).
*   `created_at`: Timestamp.

### Participant
Represents a human subject.
*   `participant_id`: Pseudonymous ID (e.g., `P-001`).
*   `condition`: String (`"enhanced"`, `"reduced"`, `"baseline"`).
*   `consent_verified`: Boolean.
*   `completion_timestamp`: Timestamp.
*   `status`: String (`"complete"`, `"partial"`, `"dropped"`).

### Response
Represents a single answer to a recognition question.
*   `response_id`: Unique identifier.
*   `participant_id`: FK to Participant.
*   `question_id`: Identifier for the question.
*   `is_false_detail`: Boolean (True if the item was a lure).
*   `lure_source_query`: String (Query used to generate the lure, e.g., "objects in kitchen not in image").
*   `response_value`: Boolean (True if participant said "Yes, I saw this").
*   `response_timestamp`: Timestamp.

## Data Flow

1.  **Ingestion**: Images fetched/generated -> `data/stimuli/` (raw + metadata).
2.  **Collection**: Participant responses -> `data/responses/` (JSON/CSV).
3.  **Analysis**: Responses + Stimuli metadata -> `data/analysis/` (ANOVA results, plots).

## Constraints

*   **PII**: No real names or emails in `data/responses/`.
*   **Integrity**: `participant_id` must be unique. `response_value` must be boolean.
*   **Versioning**: All data files checksummed.