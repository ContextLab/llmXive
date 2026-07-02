# Data Model: Evaluating the Impact of Code Generation Models on Code Security

## Overview

This document defines the schema for data artifacts generated and consumed by the pipeline. All data is stored in `data/` and versioned via checksums.

## Entity Relationship Diagram (Text)

```
[PROMPT] 1:N [GENERATED_SNIPPET] 1:N [VULNERABILITY_FINDING]
   |
   | (Source: CodeXGLUE or Handcrafted)
   |
[MANUAL_AUDIT] (Ground Truth for subset)
   |
[MODEL_SUMMARY] (Aggregated per Model)
[RUN_SUMMARY] (Pipeline metrics)
[SENSITIVITY_RESULTS] (FR-009)
```

## Data Entities

### 1. Prompt
*Source*: `data/prompts/manifest.json` (CodeXGLUE) and `data/prompts/handcrafted.json` (Internal)
- `prompt_id`: string (UUID)
- `text`: string
- `source`: string (enum: "codexglue", "handcrafted")
- `category`: string (e.g., "database", "auth", "html")
- `language`: string (e.g., "python", "javascript")
- `security_category`: string (e.g., "sql_injection", "xss", "auth", "general") - *Added to track security context fit*

### 2. HandcraftedPrompt (Specific Schema for Internal Data)
*Source*: `data/prompts/handcrafted.json`
- `prompt_id`: string (UUID)
- `text`: string
- `category`: string
- `security_pattern`: string (e.g., "sql_injection", "xss")
- `checksum`: string (SHA-256 of the prompt text)

### 3. GeneratedSnippet
*Source*: `data/generated/snippets.csv`
- `snippet_id`: string (UUID)
- `model_name`: string (enum: "starcoder-7b", "codegen-2b", "neox-1.3b")
- `prompt_id`: string (FK)
- `code`: string (raw text)
- `loc`: integer (Lines of Code)
- `generation_time`: float (seconds)
- `status`: string (enum: "success", "timeout", "failure")
- `error_message`: string (nullable)

### 4. VulnerabilityFinding
*Source*: `data/findings/raw_findings.csv`
- `finding_id`: string (UUID)
- `snippet_id`: string (FK)
- `scanner`: string (enum: "bandit", "semgrep", "codeql")
- `cwe_id`: string (e.g., "CWE-89")
- `raw_severity`: string (scanner-specific label)
- `mapped_severity`: integer (1-5 ordinal)
- `finding_text`: string
- `is_false_positive`: boolean (nullable, set after calibration)

### 5. ManualAudit
*Source*: `data/calibration/manual_audit.csv`
- `audit_id`: string (UUID)
- `snippet_id`: string (FK)
- `expert_id`: string
- `is_vulnerability`: boolean (True/False)
- `severity_confirmed`: integer (1-5 or null)
- `notes`: string
- `scanner_label`: string (to calculate FPR)

### 6. ModelSummary
*Source*: `data/results/model_summary.csv`
- `model_name`: string
- `total_snippets`: integer
- `mean_v_per_100loc`: float (FPR-corrected)
- `std_v_per_100loc`: float
- `mean_severity_rank`: float (Scanner Severity Proxy)
- `failure_count`: integer
- `zero_inflated_pct`: float (percentage of snippets with 0 vulns)
- `fpr_bandit`: float (calculated FPR)
- `fpr_semgrep`: float (calculated FPR)
- `fpr_codeql`: float (calculated FPR)

### 7. StatisticalResults
*Source*: `data/results/statistical_results.csv`
- `test_name`: string (e.g., "Kruskal-Wallis", "Dunn-PostHoc", "ZINB")
- `statistic_value`: float
- `p_value`: float
- `adjusted_p_value`: float (nullable)
- `conclusion`: string (e.g., "significant", "not significant")

### 8. RunSummary
*Source*: `data/results/run_summary.csv`
- `run_id`: string (UUID)
- `total_prompts`: integer (30)
- `total_models`: integer (3)
- `total_attempts`: integer (90)
- `successful_generations`: integer
- `successful_analyses`: integer
- `completion_rate_generation`: float (successful_generations / total_attempts)
- `completion_rate_analysis`: float (successful_analyses / successful_generations)
- `overall_completion_rate`: float (successful_analyses / total_attempts)

### 9. SensitivityResults
*Source*: `data/results/sensitivity_results.csv`
- `cutoff_rank`: integer (3, 4, or 5)
- `model_name`: string
- `high_risk_count`: integer
- `total_snippets`: integer
- `proportion_high_risk`: float

## Data Flow

1. **Ingestion**: `download.py` fetches CodeXGLUE prompts and saves `manifest.json`. `generate.py` creates `handcrafted.json` with checksums.
2. **Generation**: `generate.py` iterates models, generates code, saves `snippets.csv`.
3. **Analysis**: `analyze.py` runs scanners, saves `raw_findings.csv`.
4. **Calibration**: `calibration.py` processes manual audits, saves `manual_audit.csv`, calculates FPR.
5. **Aggregation**: `metrics.py` computes FPR-corrected V/100LOC, saves `model_summary.csv`.
6. **Inference**: `stats.py` runs tests, saves `statistical_results.csv`.
7. **Sensitivity**: `sensitivity.py` runs sweeps, saves `sensitivity_results.csv`.
8. **Summary**: `main.py` calculates `run_summary.csv` (SC-005).
9. **Visualization**: `viz.py` reads summary/stats, generates PNGs in `data/results/`.
10. **State Update**: `update_state.py` records hashes in `state.yaml`.

