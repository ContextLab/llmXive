# Participant Interaction Data Collection API Contract

**Version**: 1.0.0
**Status**: Draft
**Associated User Story**: US1 - Human Subject Study Data Collection
**Purpose**: Define the interface for collecting interaction data from participants during the bug localization study.

## 1. Overview

This API facilitates the collection of high-fidelity interaction data from human participants performing bug localization tasks. It handles session management, task assignment (via Latin-square design), interaction logging, and submission processing.

**Core Principles**:
- **Precision**: All timestamps must be recorded with millisecond precision (≤100ms error, FR-003).
- **Integrity**: Data must be immutable once logged; only append operations allowed.
- **Privacy**: No PII (Personally Identifiable Information) stored in the interaction logs.
- **Reliability**: Graceful handling of network failures and participant dropout (Edge Case).

## 2. Base URL & Versioning

All endpoints are relative to the base path: `/api/v1/participant`

```text
Base URL: <backend-host>/api/v1/participant
Content-Type: application/json
```

## 3. Authentication & Session Management

Participants do not use traditional authentication (username/password). Instead, they are identified via a generated `session_token` issued upon the first interaction.

### 3.1 Session Creation

**Endpoint**: `POST /session/start`

**Description**: Initializes a new study session for a participant. This is the first call a participant must make. It validates the participant's consent (if provided via a separate pre-study flow) and assigns a unique `session_id`.

**Request Body**:
```json
{
 "participant_code": "string", // Optional: Pre-assigned code if known, otherwise null
 "consent_verified": "boolean" // Must be true if consent was collected externally
}
```

**Response (201 Created)**:
```json
{
 "session_id": "uuid-v4-string",
 "session_token": "string", // Bearer token for subsequent requests
 "expires_at": "ISO-8601-datetime",
 "assigned_condition": "string" // e.g., "baseline", "llm_sim", "rule"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid `participant_code` format or `consent_verified` is false.
- `409 Conflict`: Participant already has an active session.

### 3.2 Session Heartbeat

**Endpoint**: `POST /session/heartbeat`

**Description**: Keeps the session alive. Required if a participant is idle for >5 minutes to prevent premature timeout.

**Headers**:
- `Authorization: Bearer <session_token>`

**Response (200 OK)**:
```json
{
 "status": "active",
 "expires_at": "ISO-8601-datetime" // Updated expiry
}
```

### 3.3 Session Termination

**Endpoint**: `POST /session/end`

**Description**: Explicitly ends the study session. Called when a participant finishes all tasks or voluntarily drops out.

**Headers**:
- `Authorization: Bearer <session_token>`

**Request Body**:
```json
{
 "completion_status": "completed" | "dropped_out",
 "final_task_id": "string" // Optional: ID of the last task worked on
}
```

**Response (200 OK)**:
```json
{
 "status": "session_terminated",
 "message": "Thank you for participating."
}
```

## 4. Task Retrieval

**Endpoint**: `GET /task/next`

**Description**: Retrieves the next available bug localization task for the current participant based on the Latin-square assignment logic.

**Headers**:
- `Authorization: Bearer <session_token>`

**Response (200 OK)**:
```json
{
 "task_id": "string", // Unique identifier for the buggy method
 "method_name": "string",
 "file_path": "string",
 "source_code": "string", // The full method source code
 "condition": "string", // "baseline", "llm_sim", or "rule"
 "summary_payload": {
 "type": "string", // "none", "llm_sim", "rule"
 "content": "string" // The summary text to display, or null
 },
 "ground_truth": {
 "buggy_line": "integer", // Line number (1-based) - NOT exposed to client in production, used for backend validation only
 "expected_context": "string"
 }
}
```

**Note**: The `ground_truth` object is included in the API response for the purpose of the *backend* validation logic upon submission, but the `buggy_line` must be masked or handled securely if this API is exposed to a public client. In a strict separation, the backend should only store the ID and validate against the internal database, not return the answer. *Correction*: The API returns the task context. The `ground_truth` is **NOT** returned to the client. The client only receives `task_id` and `source_code`. The backend stores the ground truth separately and validates the submission against it.

**Corrected Response (200 OK)**:
```json
{
 "task_id": "string",
 "method_name": "string",
 "file_path": "string",
 "source_code": "string",
 "condition": "string",
 "summary_payload": {
 "type": "string",
 "content": "string"
 }
}
```

## 5. Interaction Logging

**Endpoint**: `POST /interaction/log`

**Description**: Records a single interaction event (e.g., scrolling, line selection, time elapsed). This endpoint is called frequently (high cardinality).

**Headers**:
- `Authorization: Bearer <session_token>`

**Request Body**:
```json
{
 "task_id": "string",
 "event_type": "line_selected" | "view_scrolled" | "summary_viewed" | "timer_tick",
 "timestamp_ms": "integer", // Unix epoch in milliseconds
 "payload": {
 "selected_line": "integer", // Only for line_selected
 "scroll_position": "integer", // Only for view_scrolled
 "duration_ms": "integer" // Only for timer_tick
 }
}
```

**Response (201 Created)**:
```json
{
 "log_id": "uuid-v4-string",
 "status": "recorded"
}
```

**Validation Rules**:
- `timestamp_ms` must be strictly greater than the previous event's timestamp for the same session.
- `selected_line` must be within the bounds of `source_code` lines.

## 6. Task Submission

**Endpoint**: `POST /task/submit`

**Description**: Submits the participant's final decision for a task. This triggers the evaluation logic.

**Headers**:
- `Authorization: Bearer <session_token>`

**Request Body**:
```json
{
 "task_id": "string",
 "selected_line": "integer", // The line number the participant believes is buggy
 "time_to_decision_ms": "integer", // Total time spent on this task
 "confidence_rating": "integer" // 1-5 scale
}
```

**Response (200 OK)**:
```json
{
 "submission_id": "uuid-v4-string",
 "is_correct": "boolean", // Calculated by comparing selected_line vs ground_truth
 "feedback": "string" // Optional: "Correct" or "Incorrect" (if immediate feedback is enabled)
}
```

**Backend Logic**:
1. Retrieve `ground_truth_line` for `task_id`.
2. Compare `selected_line` with `ground_truth_line`.
3. Log the result to `data/interaction_logs/raw_logs.csv` (via `code/utils/interaction_logger.py`).
4. Mark the task as completed for this participant.

## 7. Data Models (Internal Representation)

The API persists data to match the `InteractionLog` model defined in `code/utils/models.py`:

```python
@dataclass
class InteractionLog:
 participant_id: str # Anonymized ID derived from session
 task_id: str
 condition: str # baseline, llm_sim, rule
 timestamp_ms: int
 selected_line: Optional[int]
 ground_truth_line: int # Stored internally, not exposed
 is_correct: bool # Derived
 dropout_flag: bool # If session ended prematurely
```

## 8. Error Handling Standards

All error responses follow this format:

```json
{
 "error_code": "string", // e.g., "VALIDATION_ERROR", "SESSION_EXPIRED"
 "message": "string", // Human-readable description
 "details": {} // Optional technical details
}
```

**Common Error Codes**:
- `SESSION_EXPIRED`: Token has timed out.
- `INVALID_TASK`: Task ID does not exist or is already completed.
- `VALIDATION_ERROR`: Request body fails schema validation.
- `RATE_LIMITED`: Too many requests in a short window.

## 9. Security & Compliance

- **Transport Security**: All endpoints must be served over HTTPS.
- **Data Minimization**: Only collect data strictly necessary for the study (line selection, timestamps).
- **Anonymization**: The `participant_code` is used for session creation but is immediately hashed to generate an internal `participant_id` before storage.
- **Consent**: The `consent_verified` flag must be true before any data is accepted.

## 10. Implementation Notes

- **Latency**: The `/interaction/log` endpoint must be optimized for low latency to avoid impacting the user experience. Consider asynchronous writing to the CSV file (buffered writes).
- **Concurrency**: The system must handle multiple concurrent participants. The `assignment_generator` logic must be thread-safe when assigning tasks.
- **Fallback**: If the database or file system is unavailable, the API should return a `503 Service Unavailable` and not lose the interaction data (queue it for retry if possible, or prompt the user to refresh).