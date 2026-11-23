# Data Model: Evaluating the Impact of LLM-Generated Code Documentation on Developer Onboarding

## 1. Entity Relationship Overview

The data model consists of three primary entities: `Repository`, `Participant`, and `TaskSession`.
*   **Repository**: The codebase being studied (one-to-many with TaskSessions).
*   **Participant**: The human subject (one-to-many with TaskSessions).
*   **TaskSession**: A single onboarding attempt (one-to-many with ClarificationQuestions).

## 2. Entity Definitions

### 2.1 Repository
Represents the open-source project selected for the study.
*   **Attributes**:
    *   `repo_id`: Unique identifier (UUID).
    *   `url`: GitHub URL.
    *   `commit_hash`: Pinned commit SHA (string).
    *   `condition`: Enum {`llm_docs`, `human_docs`, `no_docs`}.
    *   `loc`: Lines of Code (integer).
    *   `cc`: Cyclomatic Complexity (integer).
    *   `doc_quality_score`: Float (0.0-1.0) based on rubric.
    *   `generated_docs_path`: Relative path to generated Markdown.

### 2.2 Participant
Represents a recruited volunteer.
*   **Attributes**:
    *   `participant_id`: Anonymized UUID.
    *   `condition`: Enum {`llm_docs`, `human_docs`, `no_docs`}.
    *   `demographics`: Optional JSON (age, experience level).
    *   `status`: Enum {`active`, `completed`, `dropped_out`}.
    *   `consent_timestamp`: ISO 8601 datetime.

### 2.3 TaskSession
Represents a single onboarding task attempt by a participant on a repository.
*   **Attributes**:
    *   `session_id`: Unique UUID.
    *   `participant_id`: FK to Participant.
    *   `repo_id`: FK to Repository.
    *   `start_time`: ISO 8601 datetime.
    *   `end_time`: ISO 8601 datetime (or null if incomplete).
    *   `duration_seconds`: Integer (calculated).
    *   `status`: Enum {`completed`, `failed`, `stopped`}.
    *   `max_time_flag`: Boolean (true if stopped at 45m).
    *   `helpfulness_rating`: Integer (1-5) or null.

### 2.4 ClarificationQuestion
Represents a query made by a participant during the session.
*   **Attributes**:
    *   `question_id`: Unique UUID.
    *   `session_id`: FK to TaskSession.
    *   `timestamp`: ISO 8601 datetime.
    *   `content`: String (text of the question).
    *   `type`: Enum {`clarification`, `moderator_action`}.

## 3. Data Flow

1.  **Ingestion**: Repositories are fetched, metrics (LOC, CC) calculated, and stored in `data/raw/repo_metrics.json`.
2.  **Generation**: LLM generates docs (or human docs are verified) and stored in `data/raw/generated_docs/`.
3.  **Experiment**: Participants run tasks; logs are written to `data/raw/participant_logs.json` in real-time.
4.  **Anonymization**: Script strips PII from `participant_logs.json` and writes to `data/processed/anonymized_logs.json`.
5.  **Analysis**: `analyze.py` reads `data/processed/anonymized_logs.json` and outputs `data/processed/results.json`.

## 4. Validation Rules

*   **Commit Hash**: Must be a valid 40-character SHA-1 string.
*   **Timestamps**: Must be valid ISO 8601; `end_time` >= `start_time`.
*   **Ratings**: Must be integers in range [1, 5].
*   **Conditions**: Must be one of the three valid conditions.

