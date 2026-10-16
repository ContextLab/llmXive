# Data Model: llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

## Core Entities

| Entity | Description | Primary Fields |
|--------|-------------|----------------|
| **CodeInstance** | One code snippet (real from TIDE or synthetic) with its source and ground‑truth label. | `instance_id` (str), `source_code` (str), `ground_truth_label` (bool), `origin` (`real`/`synthetic`) |
| **FeatureRecord** | Quantitative structural metrics extracted from a `CodeInstance`. | `instance_id` (ref), `dependency_depth` (int, 0‑5), `semantic_scope` (`local`/`cross_module`), `syntactic_complexity` (int), `ast_depth` (int), `import_count` (int), `cyclomatic_complexity` (int) |
| **DetectionResult** | Outcome of a single pipeline run on a `CodeInstance`. | `instance_id` (ref), `pipeline` (`tide_lite`/`tide_original`), `prediction` (bool), `latency_ms` (float) |
| **AnalysisSummary** | High‑level results from statistical analyses. | `logistic_coefficients` (dict), `auc_mean` (float), `thresholds` (dict of feature → value), `threshold_ci` (dict), `mcnemar_pvalues` (dict per bin), `corrected_pvalues` (dict), `sensitivity_variance` (float), `efficiency` (dict) |

## File Formats

| File | Format | Schema Reference |
|------|--------|------------------|
| `data/features.csv` | CSV (UTF‑8) | `contracts/detection_results.schema.yaml` (FeatureRecord subset) |
| `data/tide_lite_enriched.csv` | CSV | `contracts/detection_results.schema.yaml` (full) |
| `data/tide_original_enriched.csv` | CSV | `contracts/detection_results.schema.yaml` (full) |
| `data/merged_results.csv` | CSV (joined FeatureRecord + both DetectionResult rows) | `contracts/detection_results.schema.yaml` (full) |
| `analysis/logistic_summary.json` | JSON (human‑readable) | N/A |
| `analysis/mcnemar_results.csv` | CSV | N/A |
| `analysis/sensitivity_summary.csv` | CSV | N/A |
| `analysis/efficiency_report.json` | JSON | N/A |

All CSVs include a `sha256` column containing the SHA‑256 checksum of the concatenated row values (ensuring Principle III compliance). The `origin` field is retained throughout to control for real vs. synthetic effects.

---
