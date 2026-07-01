# Data Model: Data Journalist Agent

## 1. Overview

This document defines the data structures used by the `data2story-skill` pipeline during the reproduction phase. The primary data artifacts are the **Scenario Input**, **Cell Registry**, **Audit Report**, **Multimodal Asset Metadata**, and the **Gold Standard**.

## 2. Core Entities

### 2.1 Scenario (Input)
The input to the pipeline is a Markdown/YAML file describing the news topic and data source.

```yaml
# Example: 01_meteorite_flagship.md structure
title: "Meteorite Landings in the 20th Century"
data_source: "local_data/meteorites.csv"
claims:
  - "The largest meteorite landed in Namibia."
  - "Most meteorites fell in the 1990s."
  # ...
```

### 2.2 Gold Standard (Input/Validation)
A manually curated list of expected claims for the scenario, used as the ground truth for validation.
*   **Source**: `gold_standard_claims.json`
*   **Format**: `{"claims": ["claim_text_1", "claim_text_2", ...]}`

### 2.3 Cell Registry (Output)
The central artifact for evidence traceability. Maps story claims to data cells.

**Schema**: `contracts/cell_registry.schema.yaml` (See below)

### 2.4 Audit Report (Output)
Summary of the pipeline execution, including success rates, error logs, and **Gold Standard metrics**.

**Schema**: `contracts/audit_report.schema.yaml` (See below)

### 2.5 Multimodal Asset (Output)
Metadata for generated images, audio, or video.

**Schema**: `contracts/asset_metadata.schema.yaml` (See below)

### 2.6 Execution Status (Entity)
Defines the possible states of the pipeline execution.
*   **Enum Values**: `success`, `partial_success`, `failed`, `NEEDS_CLARIFICATION`.
*   **Usage**: Used in `audit_report.json` to indicate if the pipeline completed or if clarification is needed (e.g., missing data).

## 3. Data Flow

1.  **Input**: `Scenario` file.
2.  **Processing**:
    *   `Detective` extracts claims -> `Claim List`.
    *   `Analyst` queries `data_source` -> `Evidence Map`.
    *   `Designer` requests assets -> `Asset Requests`.
3.  **Validation**:
    *   `Inspector` compares `Claim List` vs `Gold Standard`.
4.  **Output**:
    *   `Cell Registry` (Claims + Evidence).
    *   `Assets` (Images/Audio).
    *   `Audit Report` (Metrics including Recall/Precision).

## 4. Constraints

*   **Traceability**: Every claim in the registry must have a `source_id` that exists in the raw data.
*   **Validation**: The `Inspector` agent must verify that `source_id` is valid before finalizing the registry.
*   **Fallback**: If asset generation fails, the `asset_metadata` must include `status: "placeholder"` and `generation_mode: "fallback"`.
*   **Status Codes**: The `audit_report` must support `status: "NEEDS_CLARIFICATION"` if data is missing.