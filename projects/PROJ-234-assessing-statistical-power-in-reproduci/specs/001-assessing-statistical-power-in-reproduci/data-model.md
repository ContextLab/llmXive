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
| `task_id` | integer \| null | Associated OpenML task ID (may be null). |
| `task_type` | string \| null | e.g., “Binary Classification”. |
| `class_distribution` | object \| null | Mapping class → count (if available). |
| `downloaded_at` | string (date‑time) | ISO‑8601 timestamp of API fetch. |
| `oa_status` | string (`open_access` | `paywalled` | `no_link`) | OA determination. |
| `status` | string (`active` | `archived` | `unparseable`) | Pipeline status. |

### 2.2 StatisticalParameters
| Field | Type | Description |
|---|---|---|
| `dataset_id` | integer | FK to `DatasetMetadata`. |
| `sample_size` | number | Total N reported in the paper. |
| `effect_size` | number | Cohen’s d, F, or odds ratio (standardized). |
| `metric_type` | string (`Cohen's d` | `F` | `odds_ratio`) | Type of effect size. |
| `degrees_of_freedom` | object \| null | `{ "num": int, "den": int }` for F‑statistics. |
| `validation_status` | string (`valid` | `invalid_metric` | `ambiguous`) | Extraction quality flag. |
| `extraction_pass` | string (`full_text` | `abstract`) | Which source yielded the match. |
| `extraction_confidence` | string (`high` | `medium` | `low`) | Confidence based on regex match length. |
| `source_text_snippet` | string | Raw snippet that triggered extraction. |

### 2.3 PowerAuditResult
| Field | Type | Description |
|---|---|---|
| `dataset_id` | integer | FK to `DatasetMetadata`. |
| `observed_power` | number (0‑1) | Observed statistical power calculated from extracted parameters. |
| `target_power` | number | Power level used for a priori checks (default 0.8). |
| `threshold_met` | boolean | `True` if observed power ≥ 0.8 (adequate). |
| `status` | string (`success` | `paywalled` | `unparseable` | `skipped`) | Outcome of the calculation. |
| `alpha` | number | Significance level used (default 0.05). |
| `test_type` | string (`t-test` | `anova` | `logistic`) | Statistical test assumed for the power calculation. |
| `weighted_power` | number (0‑1) \| null | Power value after applying quintile weighting (optional, present only in weighted summary file). |

### 2.4 ExtractionAuditReport
| Field | Type | Description |
|---|---|---|
| `total_datasets` | integer | Number of datasets retrieved from OpenML. |
| `oa_count` | integer | Datasets with OA links. |
| `paywalled_count` | integer | Datasets with paywalled links. |
| `extraction_success_full_text` | integer | Successful extractions from full text. |
| `extraction_success_abstract` | integer | Successful extractions from abstract (fallback). |
| `sensitivity_delta` | number | Difference in success rates (full – abstract). |
| `extraction_success_rate` | number (0‑1) | `(successes / oa_count)`. |
| `dataset_type_distribution` | object | `{ "binary": int, "multiclass": int }`. |
| `source_category_distribution` | object | Counts per source category (e.g., arXiv, PubMed Central). |
| `precision` | number (0‑1) | Precision of extraction on the validation set. |
| `recall` | number (0‑1) | Recall of extraction on the 15‑paper validation set. |
| `f1_score` | number (0‑1) | F1 of extraction on the 15‑paper validation set. |

## 3. Data Flow Diagram
1. **Ingest** → `data/raw/openml_raw.json` (immutable).  
2. **Filter & OA Check** → `data/processed/filtered_datasets.csv` (validated against `DatasetMetadata` schema).  
3. **Parse** → `data/processed/statistical_params.json` (validated against `StatisticalParameters` schema – defined inline).  
4. **Observed Power Compute** → `data/processed/observed_power.csv` (validated against `PowerAuditResult` schema).  
5. **Extraction Audit Report** → `data/processed/extraction_audit_report.json` (conforms to `ExtractionAuditReport` definition).  
6. **Report** → `data/processed/audit_report.html` (visual + summary).  

All files have SHA‑256 checksums stored in `data/metadata.json`.

## 4. Constraints
- **Immutability**: Files under `data/raw/` are never overwritten.  
- **Checksums**: Every artifact’s checksum is recorded; any mismatch fails CI.  
- **No PII**: OpenML metadata is assumed clean; no personal data is stored.  
- **OA‑Only**: No attempt is made to scrape paywalled PDFs; such entries are flagged `paywalled`.  

---


