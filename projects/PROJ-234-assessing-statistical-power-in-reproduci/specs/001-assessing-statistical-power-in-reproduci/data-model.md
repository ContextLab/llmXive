# Data Model: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Overview

This document defines the data structures used throughout the pipeline. All data is persisted in `data/` and validated against schemas in `contracts/`.

## 2. Entity Definitions

### 2.1. DatasetMetadata
Represents a single entry from the OpenML API.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `dataset_id` | `int` | Unique OpenML identifier. | API |
| `name` | `str` | Human-readable dataset name. | API |
| `download_count` | `int` | Number of times downloaded. | API |
| `publication_link` | `str` | URL to the primary publication (may be null). | API |
| `task_id` | `int` | Associated task ID (may be null). | API |
| `task_type` | `str` | e.g., "Binary Classification", "Multi-class". | API |
| `class_distribution` | `dict` | e.g., `{"class_0": 100, "class_1": 50}`. | API |
| `downloaded_at` | `str` | ISO 8601 timestamp of retrieval. | System |
| `oa_status` | `str` | `open_access`, `paywalled`, `no_link`. | OA Checker |
| `status` | `str` | `active`, `archived`, or `unparseable`. | Pipeline |

### 2.2. StatisticalParameters
Represents extracted values from a publication.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `dataset_id` | `int` | FK to `DatasetMetadata`. | Pipeline |
| `sample_size` | `float` | Total N. | Parser |
| `effect_size` | `float` | Cohen's d, F, or r value. | Parser |
| `metric_type` | `str` | `Cohen's d`, `F`, `r`. | Parser |
| `degrees_of_freedom` | `dict` | Optional: `{"num": int, "den": int}` for F. | Parser |
| `validation_status` | `str` | `valid`, `invalid_metric`, `ambiguous`. | Parser |
| `extraction_pass` | `str` | `full_text`, `abstract`. | Parser |
| `extraction_confidence` | `str` | `high`, `medium`, `low`. | Parser |
| `source_text_snippet` | `str` | The raw text snippet that triggered the match. | Parser |

### 2.3. PowerAuditResult
Represents the final MDES calculation for a dataset.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `dataset_id` | `int` | FK to `DatasetMetadata`. | Pipeline |
| `calculated_mdes` | `float` | Minimum Detectable Effect Size (e.g., Cohen's d). | `statsmodels` |
| `target_power` | `float` | Target power used (default 0.8). | Config |
| `threshold_met` | `bool` | `True` if MDES <= 0.5 (example threshold for "small"). | Pipeline |
| `status` | `str` | `success`, `paywalled`, `unparseable`, `skipped`. | Pipeline |
| `alpha` | `float` | Significance level used (default 0.05). | Config |
| `test_type` | `str` | `t-test`, `anova`, `z-test`. | Config |

### 2.4. ExtractionAuditReport
Aggregated metrics for FR-008 and SC-001.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `total_datasets` | `int` | Total datasets in the audit. | Pipeline |
| `oa_count` | `int` | Datasets with OA links. | Pipeline |
| `paywalled_count` | `int` | Datasets with paywalled links. | Pipeline |
| `extraction_success_full_text` | `int` | Successful extractions from full text. | Pipeline |
| `extraction_success_abstract` | `int` | Successful extractions from abstract. | Pipeline |
| `sensitivity_delta` | `float` | Difference in success rates (Full Text - Abstract). | Pipeline |
| `extraction_success_rate` | `float` | (Success / Total OA) as a percentage. | Pipeline |

## 3. Data Flow

1.  **Ingest**: `01_ingest_openml.py` fetches raw JSON from OpenML $\to$ `data/raw/openml_raw.json`.
2.  **Filter & Check OA**: Filter for `publication_link` OR `task_id` and check OA status $\to$ `data/processed/filtered_datasets.csv`.
3.  **Parse**: `02_parse_publications.py` reads filtered list, fetches OA text, extracts params $\to$ `data/processed/statistical_params.json`.
4.  **Compute**: `03_compute_sensitivity.py` reads params, calculates MDES $\to$ `data/processed/mdes_results.csv`.
5.  **Report**: `04_generate_report.py` aggregates results $\to$ `data/processed/audit_report.html` (or PDF).

## 4. Constraints

- **Immutable Raw Data**: `data/raw/` files are never modified.
- **Checksums**: Every file in `data/` must have a corresponding SHA-256 hash in `data/metadata.json`.
- **PII**: No PII allowed in `data/`. OpenML metadata is assumed clean.
- **OA Only**: No extraction from paywalled content.
