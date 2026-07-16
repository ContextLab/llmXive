# Data Schema Reference

This document provides a comprehensive reference for all data structures used in the cognitive mechanisms pipeline. All schemas are implemented using Pydantic models in `code/utils/schema.py` to ensure type safety and validation.

## Table of Contents

1. [Enum Definitions](#enum-definitions)
2. [MFQ Schemas](#mfq-schemas)
3. [Moral Stories Schemas](#moral-stories-schemas)
4. [VR Interaction Schemas](#vr-interaction-schemas)
5. [Merged Dataset Schema](#merged-dataset-schema)
6. [Validation Rules](#validation-rules)

---

## Enum Definitions

### `SalienceLevel`
Defines the visual salience level for VR scenes.

| Value | Description |
|-------|-------------|
| `LOW` | Minimal visual cues, background elements only |
| `HIGH` | Enhanced visual cues, prominent foreground elements |

**Usage**:
```python
from code.utils.schema import SalienceLevel
level = SalienceLevel.HIGH
```

---

## MFQ Schemas

### `MFQResponse`
Represents a single response to a Moral Foundations Questionnaire item.

**Fields**:
- `respondent_id` (str): Unique identifier for the participant.
- `foundation` (str): The moral foundation being assessed. Must be one of:
 - `Care`
 - `Fairness`
 - `Loyalty`
 - `Authority`
 - `Purity`
- `score` (float): The participant's rating on a 0-5 Likert scale.
- `item_text` (str): The full text of the questionnaire item.

**Validation Rules**:
- `score` must be between 0.0 and 5.0 (inclusive).
- `foundation` must match one of the allowed strings (case-insensitive).

**Example**:
```json
{
 "respondent_id": "P001",
 "foundation": "Care",
 "score": 4.5,
 "item_text": "Whether or not someone was cruel to animals."
}
```

### `MFQDataset`
Container for a complete MFQ dataset.

**Fields**:
- `metadata` (Dict[str, Any]): Dataset metadata including:
 - `source`: Data origin (e.g., "synthetic", "osf", "huggingface")
 - `date`: Generation/collection date (ISO 8601)
 - `n`: Number of respondents
 - `seed`: Random seed used (if synthetic)
- `responses` (List[MFQResponse]): List of all responses.

**Validation**:
- All responses must have unique `respondent_id` + `foundation` pairs.
- Metadata `n` must match the count of unique `respondent_id`s.

---

## Moral Stories Schemas

### `MoralStory`
Represents a single moral dilemma scenario.

**Fields**:
- `story_id` (str): Unique identifier (e.g., "S001").
- `scenario_text` (str): The full text of the moral dilemma.
- `foundation_violated` (str): The primary moral foundation violated in the scenario.
- `severity` (float): Pre-rated severity of the violation (1.0 - 10.0).
- `ground_truth_effect` (float, optional): The known effect size for simulation validation.

**Validation Rules**:
- `severity` must be between 1.0 and 10.0.
- `scenario_text` must not be empty.

### `MoralStoriesDataset`
Container for the collection of moral stories.

**Fields**:
- `metadata` (Dict[str, Any]): Collection metadata.
- `stories` (List[MoralStory]): List of story objects.

---

## VR Interaction Schemas

### `VRInteractionLog`
Records a single interaction event in the virtual environment.

**Fields**:
- `log_id` (str): Unique log identifier.
- `story_id` (str): Reference to the `MoralStory` presented.
- `respondent_id` (str): Reference to the participant.
- `response_time` (float): Time taken to make a judgment (milliseconds).
- `gaze_dwell_time` (float): Duration of visual attention on key elements (ms).
- `judgment` (float): The moral judgment score produced (0.0 - 1.0, where 1.0 is "very wrong").
- `salience_level` (SalienceLevel): The visual salience condition (LOW or HIGH).
- `timestamp` (datetime): When the interaction occurred.

**Validation Rules**:
- `response_time` must be > 0.
- `judgment` must be between 0.0 and 1.0.
- `salience_level` must be a valid `SalienceLevel` enum.

### `VRLogsDataset`
Container for the collection of VR interaction logs.

**Fields**:
- `metadata` (Dict[str, Any]): Log collection metadata.
- `logs` (List[VRInteractionLog]): List of log objects.

---

## Merged Dataset Schema

### `MergedDataset`
The final processed dataset combining MFQ scores, story details, and VR logs.

**Fields**:
- `metadata` (Dict[str, Any]): Merge operation metadata.
- `records` (List[Dict[str, Any]]): List of merged records.

**Merged Record Structure**:
Each record in `records` contains:
- `respondent_id` (str)
- `story_id` (str)
- `foundation_score` (float): Aggregated MFQ score for the relevant foundation.
- `salience_level` (str): 'low' or 'high'.
- `judgment` (float)
- `response_time` (float)
- `severity` (float)
- `ground_truth_effect` (float, optional)

**Validation**:
- Every `respondent_id` in `logs` must have a corresponding MFQ response.
- Every `story_id` in `logs` must exist in the stories dataset.

---

## Validation Rules

All schemas enforce the following constraints at runtime:

1. **Type Safety**: All fields are strictly typed. Invalid types raise `ValidationError`.
2. **Range Checks**: Numerical fields (scores, times) are validated against physical bounds.
3. **Enum Constraints**: Categorical fields (foundation, salience) accept only defined values.
4. **Referential Integrity**: Foreign keys (e.g., `story_id` in logs) are validated against source datasets.

**Example Validation Error**:
```python
from code.utils.schema import MFQResponse

try:
 response = MFQResponse(
 respondent_id="P001",
 foundation="Care",
 score=6.0, # Invalid: > 5.0
 item_text="Test"
)
except ValidationError as e:
 print(e)
# Output: 1 validation error for MFQResponse
# score
# ensure this value is less than or equal to 5.0 (type=value_error.number.not_le; limit_value=5.0)
```
