# Data Model: The Impact of Self‑Compassion on Resilience to Negative Feedback

## Entity Definitions

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **RawDataset** | Unmodified CSV/Parquet file downloaded from OSF. | `file_path`, `checksum`, `download_timestamp` |
| **CleanedDataset** | Result of FR‑002, FR‑003, FR‑004; stored as Parquet. | `file_path`, `num_rows_original`, `num_rows_cleaned`, `exclusion_log` |
| **AnalysisResult** | Output of each ANCOVA model plus robustness metrics. | `outcome`, `model_summary`, `interaction`, `partial_eta_sq`, `robust_se_flag`, `heteroskedasticity_flag`, `bootstrap_ci`, `plot_paths`, `report_path` |
| **SimpleSlopePlot** | PNG image visualizing moderation effect. | `outcome`, `file_path`, `scs_levels` |
| **HTMLReport** | Consolidated HTML document. | `file_path`, `generation_timestamp` |

## Relationships

- One **RawDataset** → one **CleanedDataset** (one‑to‑one).  
- One **CleanedDataset** → three **AnalysisResult** objects (one per outcome).  
- Each **AnalysisResult** references up to two **SimpleSlopePlot** objects (primary and robustness) and the shared **HTMLReport**.

## Schema Definitions (Pydantic)

*Implemented in `src/data/schemas.py` and validated against `contracts/analysis_result.schema.yaml`.*

---
