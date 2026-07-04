# API Contract: Participant Interaction Data Collection

**Project**: PROJ-140-evaluating-the-efficacy-of-code-summariz
**User Story**: US1 - Human Subject Study Data Collection
**Task**: T018a
**Status**: Draft

## Overview

This document defines the API contract for collecting participant interaction data during the bug localization study. The API supports session management, task assignment, and interaction logging.

## Base URL

```
/api/v1/participant
```

## Authentication

No authentication required for the study interface. Session management is handled via a unique `session_id` returned upon initialization.

## Endpoints

### 1. Initialize Session

**Endpoint**: `POST /api/v1/participant/session/init`

**Description**: Creates a new study session and assigns a participant ID and initial task based on the Latin-square design.

**Request Body**:
```json
{
 "consent_verified": true,
 "demographics": {
 "years_experience": 3,
 "primary_language": "Python",
 "education_level": "Bachelor"
 }
}
```

**Response (201 Created)**:
```json
{
 "session_id": "sess_8f3a2b1c",
 "participant_id": "p_001",
 "assigned_task": {
 "task_id": "task_defects4j_042",
 "condition": "baseline",
 "buggy_method_id": "method_042",
 "source_code": "def example_method(self, x, y):\n #... code...",
 "ground_truth_line": 15,
 "summary": "Calculates the sum of x and y"
 },
 "expires_at": "2023-10-27T10:00:00Z"
}
```

**Errors**:
- `400 Bad Request`: Invalid demographics or consent verification.
- `409 Conflict`: Participant ID already exists (duplicate submission attempt).

---

### 2. Submit Interaction

**Endpoint**: `POST /api/v1/participant/interaction`

**Description**: Records a single interaction event (line selection, time elapsed) for the current session.

**Request Body**:
```json
{
 "session_id": "sess_8f3a2b1c",
 "task_id": "task_defects4j_042",
 "condition": "baseline",
 "selected_line": 14,
 "timestamp_ms": 1698400000123,
 "latency_ms": 4500,
 "decision_type": "submit"
}
```

**Response (200 OK)**:
```json
{
 "status": "recorded",
 "interaction_id": "int_992a1b",
 "remaining_attempts": 2
}
```

**Validation**:
- `selected_line` must be an integer > 0.
- `timestamp_ms` must be a valid Unix timestamp in milliseconds.
- `session_id` must be active.

**Errors**:
- `404 Not Found`: Invalid `session_id` or `task_id`.
- `400 Bad Request`: Invalid line number or timestamp.

---

### 3. Get Next Task (Latin-Square Assignment)

**Endpoint**: `GET /api/v1/participant/session/{session_id}/next_task`

**Description**: Retrieves the next task for a participant based on the Latin-square design, ensuring balanced condition assignment across the cohort.

**Path Parameters**:
- `session_id`: The active session ID.

**Response (200 OK)**:
```json
{
 "task_id": "task_defects4j_089",
 "condition": "llm_sim",
 "buggy_method_id": "method_089",
 "source_code": "def next_method(...):...",
 "summary": "Processes input data",
 "ground_truth_line": 22
}
```

**Response (404 Not Found)**:
```json
{
 "error": "No remaining tasks for this participant condition"
}
```

---

### 4. Complete Session

**Endpoint**: `POST /api/v1/participant/session/{session_id}/complete`

**Description**: Finalizes the session, triggers data anonymization logic, and marks the participant as completed.

**Path Parameters**:
- `session_id`: The active session ID.

**Request Body**:
```json
{
 "final_feedback": "Optional text feedback"
}
```

**Response (200 OK)**:
```json
{
 "status": "completed",
 "anonymized_log_path": "data/interaction_logs/anonymized_logs.csv",
 "message": "Thank you for participating. Your data has been anonymized."
}
```

---

## Data Model (Reference)

The interaction data is structured according to the `InteractionLog` model defined in `code/utils/models.py`:

```python
@dataclass
class InteractionLog:
 participant_id: str
 task_id: str
 condition: str # 'baseline', 'llm_sim', 'rule'
 timestamp_ms: int
 selected_line: int
 ground_truth_line: int
 latency_ms: int
 session_id: str
```

## Session Management

- Sessions are time-bound (default 2 hours).
- If a session expires, the participant must re-initialize (new `session_id`), but `participant_id` remains consistent to track dropout.
- Latin-square assignment logic is managed server-side in `code/utils/assignment_generator.py`.

## Error Handling

All errors return a JSON body:
```json
{
 "error_code": "ERR_CODE",
 "message": "Human readable description"
}
```