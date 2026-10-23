# Data Model: Evaluating the Impact of Code Generation on Long-Term Code Maintainability

## Overview
All artifacts live under `data/`. Raw API dumps are immutable; processed files are versioned and validated against JSON‑Schema contracts.

## Entities

| Entity | Key Fields | Description |
|--------|------------|-------------|
| **Repository** | `repo_id`, `language`, `stars`, `created_at`, `updated_at`, `is_active`, `total_loc` | One GitHub project containing code, identified by owner/name, with metadata on activity level and topics. |
| **CodeBlock** | `block_id`, `repo_id`, `file_path`, `start_line`, `end_line`, `origin_label`, `confidence`, `complexity`, `nesting_depth`, `loc`, `introduction_commit`, `introduction_timestamp` | A function or class within a repository, characterized by its origin label (LLM/Human), initial complexity metrics, and file path. |
| **MatchedPair** | `pair_id`, `llm_block_id`, `human_block_id`, `propensity_score`, `repo_id`, `repo_stars`, `repo_total_loc` | Result of 1:1 propensity‑score matching (within repo when possible, otherwise pooled). |
| **MaintenanceEvent** | `event_id`, `block_id`, `event_type`, `timestamp`, `lines_added`, `lines_deleted`, `issue_number`, `latency_days` | Either a churn event (`event_type` = `churn`) or a bug‑fix event (`event_type` = `bug_fix`). Captures per‑commit changes and linked‑issue latency. |
| **GroundTruth** | `block_id`, `manual_label`, `verifier_id` | Human‑verified origin label for a subset of blocks. |

## Additional Metrics

| Metric | Definition | Source |
|--------|------------|--------|
| **churn_rate** | `churn_lines / loc` – normalized code churn per line of code | Computed in `code/06_metrics_extraction.py` |
| **latency_survival** | Right‑censored latency (days) with `null` indicating censored | Used in survival analysis (Kaplan‑Meier, log‑rank) |

## Data Flow
1. **Raw** – `data/raw/repos.json`, `data/raw/git_logs/`, `data/raw/issues.json` (immutable snapshots).  
2. **Processed** –  
   - `data/processed/tagged_blocks.csv` (CodeBlock + classification).  
   - `data/processed/matched_pairs.csv` (MatchedPair).  
   - `data/processed/metrics_per_pair.csv` (per‑pair churn, `churn_rate`, latency, conforms to `contracts/metrics.schema.yaml`).  
   - `data/processed/maintenance_events.csv` (individual `MaintenanceEvent` records).  
   - `data/ground_truth/manual_labels.csv` (GroundTruth).  
3. **Analysis** – `data/analysis/wilcoxon_results.json` and PNG figures under `data/analysis/figures/`.  

All CSV/JSON files must conform to the schemas in `contracts/`.

---

