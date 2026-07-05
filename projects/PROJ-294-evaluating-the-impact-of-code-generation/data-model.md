# Data Model Specification

## Metrics JSON Structure (data/analysis/metrics.json)
```json
{
 "samples": [
 {
 "task_id": "HumanEval/0",
 "human_pass_rate": 0.9,
 "generated_code": "...",
 "cyclomatic_complexity": 5,
 "halstead_volume": 120.5,
 "branch_coverage_pct": 85.2,
 "pass_rate": 1,
 "model_used": "codegen-mono-350M",
 "generation_timestamp": "2024-01-15T10:30:00Z"
 }
 ],
 "metadata": {
 "total_samples": 50,
 "generation_model": "Salesforce/codegen-mono-350M",
 "analysis_timestamp": "2024-01-15T12:00:00Z"
 }
}
```

## Artifact Hashes Structure (state/artifact_hashes.yaml)
```yaml
artifacts:
 data/raw/humaneval.json:
 sha256: "abc123..."
 verified_at: "2024-01-15T09:00:00Z"
 data/analysis/metrics.json:
 sha256: "def456..."
 verified_at: "2024-01-15T12:00:00Z"
```

## Statistical Results Structure
- Wilcoxon test results: statistic, p-value
- McNemar test results: chi-square, p-value
- Power analysis: achieved power, required sample size
- Correlation coefficients: spearman, point-biserial
