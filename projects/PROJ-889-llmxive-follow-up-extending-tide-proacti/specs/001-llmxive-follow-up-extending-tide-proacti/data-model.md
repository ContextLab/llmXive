# Data Model: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

## Core Entities

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **CodeInstance** | One code snippet (real or synthetic) with its raw source and ground‑truth label. | `instance_id` (str), `source_code` (str), `ground_truth_label` (bool), `origin` (`real`/`synthetic`) |
| **FeatureRecord** | Quantitative structural metrics extracted from a `CodeInstance`. | `instance_id` (ref), `dependency_depth` (int), `semantic_scope` (str: `local`/`cross_module`), `syntactic_complexity` (int), `ast_depth` (int), `import_count` (int), `cyclomatic_complexity` (int) |
| **DetectionResult** | Outcome of a single pipeline run on a `CodeInstance`. | `instance_id` (ref), `pipeline` (`tide_lite`/`tide_original`), `prediction` (bool), `latency_ms` (float) |
| **AnalysisSummary** | High‑level results from statistical analyses. | `logistic_coefficients` (dict), `auc_mean` (float), `threshold_point` (dict of feature values), `mcnemar_pvalues` (dict per bin), `corrected_pvalues` (dict), `sensitivity_variance` (float), `efficiency` (dict) |

## File Formats

| File | Format | Schema Reference |
|------|--------|------------------|
| `features.csv` | CSV (header row) | `contracts/detection_results.schema.yaml` (FeatureRecord subset) |
| `tide_lite_enriched.csv` | CSV | `contracts/detection_results.schema.yaml` (full schema) |
| `tide_original_enriched.csv` | CSV | `contracts/detection_results.schema.yaml` (full schema) |
| `merged_results.csv` | CSV (joined FeatureRecord + both DetectionResult rows) | `contracts/detection_results.schema.yaml` (full record) |
| `logistic_summary.json` | JSON | N/A (human‑readable) |
| `mcnemar_results.csv` | CSV | N/A |
| `sensitivity_summary.csv` | CSV | N/A |
| `efficiency_report.json` | JSON | N/A |

All CSVs are UTF‑ encoded, newline `\n`, and include a checksum column (`sha256`) for data‑hygiene compliance (Principle III). The `origin` field is included to control for real vs. synthetic source effects.

---


