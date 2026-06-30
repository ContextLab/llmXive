# Data Model: Visual Detail and False Memory Susceptibility

## Overview

This document defines the data structures used in the project, ensuring alignment with the Functional Requirements (FR-001 to FR-008) and the Project Constitution. All data is stored in `data/` with strict versioning and checksumming.

## Entities

### 1. Image (Stimulus)

Represents a baseline image and its manipulated variants.

**Attributes**:
-   `image_id`: Unique identifier (UUID).
-   `baseline_complexity_score`: Float (0.0 - 1.0). Derived from mock generator.
-   `complexity_bin`: String (Q1, Q2, Q3).
-   `baseline_path`: Relative path to the baseline image file.
-   `enhanced_path`: Relative path to the enhanced detail image.
-   `reduced_path`: Relative path to the reduced detail image.
-   `manipulation_params`: Dictionary containing:
    -   `objects_added`: List of strings (for enhanced).
    -   `objects_removed`: List of strings (for reduced).
    -   `texture_settings`: Dictionary.
-   `timestamp`: ISO 8601 timestamp.
-   `checksum`: SHA-256 hash of the image file.

**Source**: `code/stimuli/manipulator.py` (Mock Generator + PIL).

### 2. Participant Session

Represents a single experimental run.

**Attributes**:
-   `session_id`: Unique identifier (UUID).
-   `participant_id`: Pseudonymous hash (no PII).
-   `condition`: String (`enhanced`, `reduced`, `baseline`).
-   `baseline_image_id`: Reference to Image entity.
-   `start_timestamp`: ISO 8601.
-   `end_timestamp`: ISO 8601.
-   `completion_status`: String (`complete`, `partial`, `dropped`).
-   `consent_verified`: Boolean.
-   `total_false_memory_rate`: Float (0.0 - 1.0).

**Source**: `code/participants/session.py`.

### 3. Response

Represents a single answer to a recognition question.

**Attributes**:
-   `response_id`: Unique identifier (UUID).
-   `session_id`: Reference to Participant Session.
-   `question_id`: String (e.g., `Q_001`).
-   `is_false_detail`: Boolean (True if the item was a lure).
-   `response_value`: Boolean (True if participant said "Yes, it was there").
-   `response_timestamp`: ISO 8601.
-   `latency_ms`: Integer (time to answer).

**Source**: `code/participants/interface.py`.

## Data Flow

1.  **Generation**: `code/data/loader.py` generates `Image` entities (mock) and saves to `data/stimuli/`.
2.  **Manipulation**: `code/stimuli/manipulator.py` creates `enhanced` and `reduced` versions, updates `Image` metadata, and saves to `data/stimuli/`.
3.  **Simulation**: `code/participants/interface.py` simulates a session, generating `Participant Session` and `Response` entities, saving to `data/responses/`.
4.  **Aggregation**: `code/analysis/stats.py` loads responses, computes `total_false_memory_rate`, and saves aggregated data to `data/processed/`.

## Data Hygiene & Versioning

-   **Checksums**: Every file in `data/` is checksummed (SHA-256) upon creation. Checksums are recorded in `state/...yaml`.
-   **No In-Place Modification**: If an image is re-manipulated, a new file is created (e.g., `img_001_v2_enhanced.png`).
-   **PII**: `participant_id` is a hash of a random seed. No names, emails, or IPs are stored.
