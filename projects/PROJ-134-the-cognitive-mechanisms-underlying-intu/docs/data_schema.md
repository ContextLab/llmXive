# Data Schema Reference

This document provides a detailed reference for all data schemas used in the pipeline. All data structures are validated using Pydantic models to ensure consistency and integrity throughout the pipeline.

## Overview

The pipeline processes three primary data types:

1. **Moral Foundations Questionnaire (MFQ) Data**: Psychometric survey responses
2. **Moral Stories Data**: Text-based moral scenarios with ground truth judgments
3. **VR Interaction Logs**: Behavioral data from virtual environment interactions

All datasets are merged into a unified `MergedDataset` for analysis.

---

## Core Enums

### `SalienceLevel`

Represents the visual salience condition assigned to each story/VR interaction.

```python
class SalienceLevel(Enum):
 LOW = "low"
 HIGH = "high"
```

**Values**:
- `LOW`: Baseline visual condition (minimal cues)
- `HIGH`: Experimental visual condition (enhanced cues)

---

## MFQ Schemas

### `MFQResponse`

Individual response to an MFQ item.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `item_id` | str | Yes | MFQ item identifier (e.g., "mfq_01", "mfq_02") |
| `score` | int | Yes | Likert scale score (0-5) |
| `foundation` | str | Yes | Moral foundation category |

**Valid Foundations**:
- `care`
- `fairness`
- `loyalty`
- `authority`
- `purity`

**Example**:

```json
{
 "item_id": "mfq_01",
 "score": 4,
 "foundation": "care"
}
```

### `MFQDataset`

Complete MFQ dataset for a single participant.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `participant_id` | str | Yes | Unique participant identifier |
| `responses` | List[`MFQResponse`] | Yes | List of all MFQ item responses |
| `timestamp` | datetime | Yes | Data collection timestamp (ISO 8601) |

**Validation Rules**:
- `score` must be between 0 and 5 (inclusive)
- `foundation` must be one of the five valid categories
- Must contain at least one response

**Example**:

```json
{
 "participant_id": "P001",
 "responses": [
 {"item_id": "mfq_01", "score": 4, "foundation": "care"},
 {"item_id": "mfq_02", "score": 2, "foundation": "fairness"}
 ],
 "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## Moral Stories Schemas

### `MoralStory`

A single moral scenario used in the experiment.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `story_id` | str | Yes | Unique story identifier |
| `text` | str | Yes | Full text of the moral scenario |
| `foundation` | str | Yes | Primary moral foundation targeted |
| `intended_judgment` | float | Yes | Ground truth judgment score (0-1) |
| `salience_level` | `SalienceLevel` | Yes | Assigned visual salience condition |

**Validation Rules**:
- `intended_judgment` must be between 0.0 and 1.0
- `text` must be non-empty
- `foundation` must be one of the five valid categories

**Example**:

```json
{
 "story_id": "STORY_001",
 "text": "A person finds a wallet on the street and decides whether to return it.",
 "foundation": "fairness",
 "intended_judgment": 0.85,
 "salience_level": "high"
}
```

### `MoralStoriesDataset`

Collection of moral stories.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stories` | List[`MoralStory`] | Yes | List of all stories in the dataset |
| `metadata` | Dict | No | Additional dataset metadata (version, source, etc.) |

---

## VR Interaction Schemas

### `VRInteractionLog`

Behavioral data from a single VR interaction session.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `log_id` | str | Yes | Unique log identifier |
| `participant_id` | str | Yes | Participant identifier |
| `story_id` | str | Yes | Associated story identifier |
| `response_time` | float | Yes | Reaction time in seconds |
| `gaze_data` | Dict | Yes | Gaze tracking coordinates (x, y, z) |
| `judgment` | float | Yes | Recorded moral judgment (0-1) |
| `salience_level` | `SalienceLevel` | Yes | Visual salience condition |
| `timestamp` | datetime | Yes | Interaction timestamp |

**Validation Rules**:
- `response_time` must be positive (> 0)
- `judgment` must be between 0.0 and 1.0
- `gaze_data` must contain 'x', 'y', 'z' keys

**Example**:

```json
{
 "log_id": "VR_001",
 "participant_id": "P001",
 "story_id": "STORY_001",
 "response_time": 2.45,
 "gaze_data": {"x": 0.12, "y": 0.34, "z": 1.0},
 "judgment": 0.82,
 "salience_level": "high",
 "timestamp": "2024-01-15T10:35:00Z"
}
```

### `VRLogsDataset`

Collection of VR interaction logs.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `logs` | List[`VRInteractionLog`] | Yes | List of all interaction logs |
| `metadata` | Dict | No | Dataset metadata (session info, version, etc.) |

---

## Merged Dataset Schema

### `MergedDataset`

Unified dataset combining MFQ, stories, and VR logs for analysis.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `merged_rows` | List[Dict] | Yes | List of merged records |
| `metadata` | Dict | Yes | Merge metadata (source files, timestamp, etc.) |

**Merged Row Structure**:

Each row in `merged_rows` contains:

```python
{
 "participant_id": str,
 "story_id": str,
 "mfq_scores": Dict[str, float], # Average scores per foundation
 "story_text": str,
 "intended_judgment": float,
 "observed_judgment": float,
 "response_time": float,
 "salience_level": str, # "low" or "high"
 "foundation": str,
 "gaze_data": Dict,
 "timestamp": datetime
}
```

**Validation Rules**:
- All required fields must be present
- `participant_id` must match between MFQ and VR logs
- `story_id` must exist in both stories and logs

---

## Validation Functions

The `code/utils/schema.py` module provides validation helpers:

```python
from code.utils.schema import (
 validate_mfq_data,
 validate_stories_data,
 validate_vr_logs_data,
 validate_merged_data
)
```

### Usage Example

```python
from code.utils.schema import validate_mfq_data
from code.config import ensure_directories

# Validate MFQ dataset
mfq_data = {...} # Load from file
validated = validate_mfq_data(mfq_data)
if validated:
 print("MFQ data is valid")
else:
 print("MFQ data validation failed")
```

---

## File Formats

### CSV Output

Processed data is exported to CSV with the following columns:

```csv
participant_id,story_id,mfq_care,mfq_fairness,mfq_loyalty,mfq_authority,mfq_purity,
story_text,intended_judgment,observed_judgment,response_time,salience_level,
foundation,gaze_x,gaze_y,gaze_z,timestamp
```

### JSON Output

Intermediate results and model outputs are stored as JSON:

```json
{
 "pipeline_version": "1.0.0",
 "timestamp": "2024-01-15T12:00:00Z",
 "results": {
 "bayesian_model": {...},
 "regression_model": {...},
 "validation_metrics": {...}
 }
}
```

---

## Data Integrity

All derived datasets are checksummed using SHA-256 via `code/utils/hashing.py`. Checksums are stored in `state/pipeline_state.yaml`:

```yaml
artifacts:
 - path: data/processed/merged.csv
 checksum: "a1b2c3d4..."
 timestamp: "2024-01-15T12:00:00Z"
 - path: state/bayesian_results.json
 checksum: "e5f6g7h8..."
 timestamp: "2024-01-15T12:05:00Z"
```

---

## References

- **Gervais et al. (2011)**: Psychometric norms for MFQ items
- **Pydantic Documentation**: https://docs.pydantic.dev/
- **Moral Foundations Theory**: https://moralfoundations.org/
