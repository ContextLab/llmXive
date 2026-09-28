# Data Model: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

## 1. Entity-Relationship Overview

The data model consists of four primary entities:
1.  **MFQResponse**: Individual responses to the Moral Foundations Questionnaire.
2.  **MoralStory**: Metadata about the moral scenarios presented in VR.
3.  **VRInteractionLog**: Interaction data from the VR environment (salience, timing).
4.  **MergedDataset**: The joined table used for analysis.

## 2. Schema Definitions

### MFQResponse
Represents a single participant's response to the MFQ.
- **participant_id**: `string` (UUID) - Unique identifier.
- **foundation**: `string` - One of: "Care", "Fairness", "Loyalty", "Authority", "Sanctity".
- **score**: `float` - Response value (1-5 scale).
- **reversed**: `boolean` - Whether the item was reverse-scored.
- **timestamp**: `datetime` - Time of response.

### MoralStory
Represents a moral scenario.
- **story_id**: `string` - Unique identifier.
- **scenario_text**: `string` - The text of the moral story.
- **dominant_foundation**: `string` - The intended moral foundation of the story.
- **complexity_score**: `float` - Pre-calculated complexity metric.

### VRInteractionLog
Represents interaction data in the VR environment.
- **log_id**: `string` - Unique identifier.
- **participant_id**: `string` - FK to MFQResponse.
- **story_id**: `string` - FK to MoralStory.
- **salience_level**: `string` - "low" or "high".
- **blend_shape_config**: `string` - JSON string of Unity blend-shape parameters (e.g., `{"eyeOpen": 0.9, "mouthSmile": 0.2}`).
- **duration_seconds**: `float` - Time spent viewing the scenario.
- **physiological_data**: `string` - Optional JSON of heart rate/GSR (if available).

### MergedDataset
The analysis-ready table.
- **participant_id**: `string`
- **story_id**: `string`
- **foundation**: `string`
- **mfq_score**: `float`
- **salience_level**: `string` (Categorical: Low, High)
- **blend_shape_config**: `string`
- **duration_seconds**: `float`
- **dominant_foundation**: `string`

## 3. Data Flow & Transformation

1.  **Ingestion**: Raw files (Parquet/CSV) are downloaded to `data/raw/`.
2.  **Validation**: `fetch_real_data.py` validates against Pydantic schemas. If validation fails, the process halts.
3.  **Cleaning**:
    - Reverse-scored MFQ items are corrected.
    - Missing values in `salience_level` trigger a drop or imputation (documented).
    - `blend_shape_config` is parsed to extract numeric salience if needed.
4.  **Merging**: `MFQResponse` is joined with `VRInteractionLog` on `participant_id` and `story_id`.
5.  **Export**: Final `MergedDataset` is saved to `data/processed/merged_analysis.parquet`.

## 4. Constraints & Invariants

- **Uniqueness**: `participant_id` + `story_id` + `foundation` must be unique in `MergedDataset`.
- **Range**: `mfq_score` must be in [1.0, 5.0].
- **Salience**: `salience_level` must be strictly "low" or "high".
- **Immutability**: `data/raw/` files are never modified. Derivations always create new files.
