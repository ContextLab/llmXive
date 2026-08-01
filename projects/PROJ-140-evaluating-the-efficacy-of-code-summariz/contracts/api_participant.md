# API Contract: Participant Interaction Data Collection

## Overview
This document defines the API contract for collecting participant interaction data in the code summarization study. It covers endpoints, request/response schemas, and session management.

## Base URL
`/api/v1/participant`

## Endpoints

### 1. Initialize Session
**Endpoint**: `POST /session`
**Description**: Initialize a new participant session and retrieve the assigned task conditions.

**Request Body**:
```json
{
 "participant_id": "string (required, unique identifier)",
 "consent_verified": "boolean (required, true if consent form is signed)"
}
```

**Response (200 OK)**:
```json
{
 "session_id": "string (unique session identifier)",
 "participant_id": "string",
 "assigned_tasks": [
 {
 "task_id": "string",
 "condition": "string (e.g., 'LLM-Sim', 'Rule-Based', 'Baseline')",
 "code_snippet": "string (buggy code snippet)",
 "summary": "string (generated summary for the condition)"
 }
 ],
 "start_time": "ISO 8601 timestamp"
}
```

**Response (400 Bad Request)**:
```json
{
 "error": "Invalid request parameters",
 "details": "string"
}
```

---

### 2. Submit Interaction
**Endpoint**: `POST /interaction`
**Description**: Record a participant's interaction (line selection, timestamp, etc.).

**Request Body**:
```json
{
 "session_id": "string (required)",
 "task_id": "string (required)",
 "selected_line": "integer (required, 1-based line number)",
 "timestamp_ms": "integer (required, milliseconds since epoch)",
 "condition": "string (required, matches assigned condition)"
}
```

**Response (200 OK)**:
```json
{
 "status": "success",
 "message": "Interaction recorded",
 "interaction_id": "string"
}
```

**Response (404 Not Found)**:
```json
{
 "error": "Session or task not found",
 "details": "string"
}
```

---

### 3. Complete Task
**Endpoint**: `POST /task/complete`
**Description**: Mark a task as completed and retrieve the next task (if any).

**Request Body**:
```json
{
 "session_id": "string (required)",
 "task_id": "string (required)"
}
```

**Response (200 OK)**:
```json
{
 "status": "success",
 "next_task": {
 "task_id": "string",
 "condition": "string",
 "code_snippet": "string",
 "summary": "string"
 },
 "is_study_complete": "boolean"
}
```

**Response (404 Not Found)**:
```json
{
 "error": "Session or task not found",
 "details": "string"
}
```

---

### 4. End Session
**Endpoint**: `POST /session/end`
**Description**: End the participant session and finalize data collection.

**Request Body**:
```json
{
 "session_id": "string (required)"
}
```

**Response (200 OK)**:
```json
{
 "status": "success",
 "message": "Session ended",
 "total_tasks_completed": "integer"
}
```

---

## Session Management
- Sessions are identified by a unique `session_id`.
- Sessions expire after 24 hours of inactivity.
- Each participant can have only one active session at a time.
- Session data includes: `participant_id`, `assigned_tasks`, `start_time`, `completed_tasks`.

## Data Validation
- `participant_id` must be a non-empty string.
- `consent_verified` must be `true` to initialize a session.
- `selected_line` must be a positive integer within the code snippet's line range.
- `timestamp_ms` must be a valid Unix timestamp in milliseconds.
- `condition` must match one of the assigned conditions for the task.

## Error Handling
- All errors return a JSON object with `error` and `details` fields.
- HTTP status codes:
 - `200`: Success
 - `400`: Bad Request (invalid input)
 - `404`: Not Found (session/task not found)
 - `500`: Internal Server Error

## Security Considerations
- All endpoints require HTTPS.
- Participant data is anonymized before storage.
- Consent forms are stored securely (see `secure_consent_storage.py`).
- Access to raw logs is restricted to authorized personnel.