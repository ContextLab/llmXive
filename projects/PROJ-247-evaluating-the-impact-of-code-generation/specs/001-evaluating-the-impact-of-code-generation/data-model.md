# Data Model: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## 1. Entities & Relationships

### 1.1 Core Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **Repository** | A GitHub project. | `repo_id` (PK), `owner`, `name`, `stars`, `last_commit_date`, `topics`, `contributor_count`, `age_days` |
| **CodeBlock** | A function/class within a repo. | `block_id` (PK), `repo_id` (FK), `file_path`, `start_line`, `end_line`, `origin_label` (LLM/Human), `confidence_score`, `complexity_score`, `loc` |
| **MaintenanceEvent** | A change to a code block. | `event_id` (PK), `block_id` (FK), `commit_hash`, `timestamp`, `lines_added`, `lines_deleted`, `issue_id` (nullable) |
| **Issue** | A GitHub issue/PR. | `issue_id` (PK), `repo_id` (FK), `number`, `state`, `created_at`, `closed_at` |
| **MatchedPair** | A pair of LLM and Human blocks. | `pair_id` (PK), `llm_block_id` (FK), `human_block_id` (FK), `propensity_score_diff`, `repo_id` (FK) |
| **GroundTruth** | Manual verification label. | `gt_id` (PK), `block_id` (FK), `human_label` (LLM/Human), `annotator_id`, `checksum` (SHA-256) |

### 1.2 Relationships

- **Repository** (1) -- (N) **CodeBlock**
- **CodeBlock** (1) -- (N) **MaintenanceEvent**
- **Issue** (1) -- (N) **MaintenanceEvent** (via `issue_id`)
- **CodeBlock** (1) -- (1) **MatchedPair** (as `llm_block_id` or `human_block_id`)
- **CodeBlock** (1) -- (0..1) **GroundTruth**

## 2. Data Flow

1. **Ingestion**: GitHub API → `raw/repos.json`, `raw/git_logs/`
2. **Processing**: `01_data_curation.py` → `processed/tagged_blocks.csv`, `processed/matched_pairs.csv`
3. **Metric Extraction**: `02_metric_extraction.py` → `processed/maintenance_metrics.csv`
4. **Analysis**: `03_analysis.py` → `results/stats.json`, `results/figures/`
5. **Verification**: `manual_labels.csv` → `results/ground_truth_metrics.json` (Checksummed)

## 3. File Formats

### 3.1 Raw Data (Immutable)
- **Format**: JSON/Parquet
- **Storage**: `data/raw/`
- **Checksum**: SHA-256 recorded in `state/`

### 3.2 Processed Data
- **Format**: CSV/Parquet
- **Storage**: `data/processed/`
- **Derivation**: Documented in `code/` scripts.

### 3.3 Ground Truth (Versioned)
- **Format**: CSV
- **Storage**: `data/ground_truth/manual_labels.csv`
- **Checksum**: SHA-256 recorded in `state/` immediately after creation.

### 3.4 Results
- **Format**: JSON/PNG
- **Storage**: `results/`
- **Traceability**: Each stat links to a row in `processed/`.

## 4. Constraints & Validation

- **Uniqueness**: `block_id` unique per repo.
- **Referential Integrity**: `repo_id` in `CodeBlock` must exist in `Repository`.
- **Confidence Threshold**: `confidence_score` ≥ 0.8 for inclusion.
- **Balance**: Propensity score difference < 0.1 for matched pairs.
- **Null Handling**: `issue_id` can be null; excluded from latency analysis.
- **Ground Truth**: Must be checksummed and recorded in `state/`.
