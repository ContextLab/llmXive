# Data Model: Assessing Statistical Power in Reproducible Research with Public Datasets

## 1. Overview
All pipeline artifacts are stored under `projects/PROJ-234-assessing-statistical-power-in-reproduci/data/` and validated against JSON‑Schema files in `contracts/`. Immutable raw files reside in `raw/`; derived files in `processed/`. The **Single Source of Truth (SSoT)** for checksums, timestamps, and version hashes is `data/metadata.json`.

## 2. Entity Definitions

### 2.1 DatasetMetadata
| Field | Type | Description |
|---|---|---|
| `dataset_id` | integer | OpenML identifier. |
| `name` | string | Human‑readable dataset name. |
| `download_count` | integer | Number of downloads on OpenML. |
| `publication_link` | string \| null | URL to primary publication (may be null). |
| `task_id` | integer \| null | Associated task ID (may be null). |
| `task_type` | string \| null | e.g., “Binary Classification”. |
| `class_distribution` | object \| null | Distribution of classes if available. |
| `downloaded_at` | string (date‑time) | ISO‑8601 timestamp of retrieval. |
| `oa_status` | string (`open_access` | `paywalled` | `no_link`) | Open Access status of the publication link. |
| `status` | string (`active` | `archived` | `unparseable`) | Pipeline status. |

### 2.2 StatisticalParameters
| Field | Type | Description |
|---|---|---|
| `dataset_id` | integer | FK to `DatasetMetadata`. |
| `sample_size` | integer | Total N reported in the paper. |
| `effect_size` | number | Cohen’s d, F, or odds ratio (standardized). |
| `metric_type` | string (`Cohen's d` | `F` | `odds_ratio`) | Type of effect size. |
| `degrees_of_freedom` | object \| null | `{ "num": int, "den": int }` for F‑statistics. |
| `validation_status` | string (`valid` | `invalid_metric` | `ambiguous`) | Extraction quality flag. |
| `extraction_pass` | string (`full_text` | `abstract`) | Which source yielded the match. |
| `extraction_confidence` | string (`high` | `medium` | `low`) | Confidence based on match length. |
| `source_text_snippet` | string | Raw snippet that triggered extraction. |

### 2.3 PowerAuditResult
| Field | Type | Description |
|---|---|---|
| `dataset_id` | integer | FK to `DatasetMetadata`. |
| `observed_power` | number (0‑1) | Observed statistical power from reported effect size. |
| `reference_power` | number (0‑1) | Power computed with the **test‑specific small‑effect benchmark** (d = 0.2, f = 0.2, log‑odds ≈ 0.2). |
| `target_power` | number | Power level used for a priori checks (default 0.8). |
| `threshold_met` | boolean | `True` if reference_power ≥ 0.8 (primary adequacy criterion). |
| `status` | string (`success` | `paywalled` | `unparseable` | `skipped`) | Outcome of the calculation. |
| `alpha` | number | Significance level used (default 0.05). |
| `test_type` | string (`t-test` | `anova` | `logistic`) | Statistical test assumed. |
| `weighted_power` | number (0‑1) \| null | Power after applying quintile weighting (optional). |
| `extraction_audit_report_path` | string | Path to the `ExtractionAuditReport` JSON (currently `reports/extraction_audit.json`). |

### 2.4 ExtractionAuditReport
| Field | Type | Description |
|---|---|---|
| `total_datasets` | integer | Number of datasets retrieved from OpenML. |
| `oa_count` | integer | Datasets with OA links. |
| `paywalled_count` | integer | Datasets with paywalled links. |
| `extraction_success_full_text` | integer | Successful extractions from full‑text. |
| `extraction_success_abstract` | integer | Successful extractions from abstract fallback. |
| `sensitivity_delta` | number | Difference in success rates (full – abstract). |
| `extraction_success_rate` | number (0‑1) | `successes / oa_count`. |
| `precision` | number (0‑1) | Precision on the validation set of papers. |
| `recall` | number (0‑1) | Recall on the validation set of papers. |
| `f1_score` | number (0‑1) | F1 on the validation set of papers. |

## 3. Data Flow Diagram
1. **Ingest** → `data/raw/openml_raw.json` (immutable).  
2. **Filter & OA Check** → `data/processed/filtered_datasets.csv` (validated against `DatasetMetadata` schema).  
3. **Parse** → `data/processed/statistical_params.json` (validated against `StatisticalParameters` schema).  
4. **Observed Power Compute** → `data/processed/observed_power.csv` (validated against `PowerAuditResult` schema, includes `reference_power`).  
5. **Extraction Audit Report** → `reports/extraction_audit.json` (conforms to `ExtractionAuditReport` definition).  
6. **Report** → `data/processed/audit_report.html` (visual + summary).  

All files have SHA‑256 checksums recorded in `data/metadata.json`.

## 4. Constraints
- **Immutability**: Files under `data/raw/` are never overwritten.  
- **Checksums**: Every artifact’s checksum is recorded; any mismatch fails CI.  
- **No PII**: OpenML metadata is assumed clean; no personal data is stored.  
- **OA‑Only**: Paywalled PDFs are not fetched; such entries are flagged `paywalled`.  

**Schema Availability**  
The schemas for `StatisticalParameters` and `ExtractionAuditReport` are defined within `contracts/power_audit_result.schema.yaml` under `$defs`. Contract tests reference these embedded definitions, satisfying the requirement that all intermediate files are validated against schemas in `contracts/`.

---


