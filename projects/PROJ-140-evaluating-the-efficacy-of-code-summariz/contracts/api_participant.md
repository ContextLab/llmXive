# API Contract: Participant Interaction Data Collection

**Version**: 1.0.0
**Status**: Draft (Implemented in T018b)
**Related User Story**: US1 - Human Subject Study Data Collection

## Overview

This document defines the API contract for collecting interaction data from participants during the bug localization study. The API supports session management, task assignment, and interaction logging.

## Base URL

All endpoints are relative to the backend server base URL.

## Endpoints

### 1. Initialize Session

**POST** `/api/participant/session/init`

Initializes a new study session for a participant.

**Request Body**:
```json
{
 "participant_id": "string (UUID)",
 "consent_verified": "boolean"
}
```

**Response**: `200 OK`
```json
{
 "session_id": "string (UUID)",
 "assigned_tasks": [
 {
 "task_id": "string",
 "condition": "string (llm_sim | rule | baseline)",
 "buggy_method_id": "string",
 "source_code": "string",
 "summary": "string (optional, based on condition)"
 }
 ],
 "latin_square_assignment": "string"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid participant_id or missing consent
- `409 Conflict`: Participant already has an active session

---

### 2. Submit Interaction

**POST** `/api/participant/interaction`

Logs a single interaction event (line selection, timestamp, etc.).

**Request Body**:
```json
{
 "session_id": "string (UUID)",
 "task_id": "string",
 "condition": "string",
 "timestamp_ms": "integer",
 "selected_line": "integer",
 "ground_truth_line": "integer",
 "latency_ms": "integer"
}
```

**Response**: `200 OK`
```json
{
 "status": "recorded",
 "interaction_id": "string (UUID)"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid schema or missing required fields
- `404 Not Found`: Session ID does not exist
- `409 Conflict`: Task already completed for this session

---

### 3. Complete Task

**POST** `/api/participant/task/complete`

Marks a specific task as completed and finalizes the interaction log for that task.

**Request Body**:
```json
{
 "session_id": "string (UUID)",
 "task_id": "string",
 "final_selected_line": "integer",
 "time_to_decision_ms": "integer"
}
```

**Response**: `200 OK`
```json
{
 "status": "completed",
 "next_task_available": "boolean"
}
```

---

### 4. End Session

**POST** `/api/participant/session/end`

Finalizes the participant session and triggers anonymization pipeline.

**Request Body**:
```json
{
 "session_id": "string (UUID)",
 "dropout_flag": "boolean (optional)"
}
```

**Response**: `200 OK`
```json
{
 "status": "ended",
 "anonymized_log_path": "string (internal path)"
}
```

---

## Session Management

- Sessions are identified by a UUID (`session_id`).
- A session remains active until explicitly ended or timed out (configurable).
- Task assignments are determined by the Latin-square design logic (see `code/utils/assignment_generator.py`).

## Data Schema Definitions

### InteractionLog
| Field | Type | Description |
|-------|------|-------------|
| participant_id | UUID | Anonymized participant identifier |
| task_id | string | Unique identifier for the bug localization task |
| condition | string | Study condition: 'llm_sim', 'rule', or 'baseline' |
| timestamp_ms | integer | Unix timestamp in milliseconds |
| selected_line | integer | 1-based line number selected by participant |
| ground_truth_line | integer | 1-based line number of the actual bug |
| latency_ms | integer | Time taken to make the selection |

## Error Handling

All errors follow the standard JSON API error format:
```json
{
 "error": "string",
 "message": "string",
 "code": "integer"
}
```
