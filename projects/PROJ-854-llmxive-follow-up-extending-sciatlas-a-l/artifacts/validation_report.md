# Pipeline Validation Report

**Generated**: 2023-10-27T14:30:00.000000
**Overall Status**: ❌ FAIL

## Execution Log

### ✅ Setup Project Structure
- **Status**: success
- **Exit Code**: 0
- **Duration**: 0.45s

### ❌ Ingest and Build Subgraph
- **Status**: failed
- **Exit Code**: 1
- **Duration**: 12.30s
- **Error**: ConnectionTimeout: Failed to fetch data from OpenAlex API. Network unreachable or rate limited.

### ❌ Generate Final Dataset
- **Status**: failed
- **Exit Code**: 1
- **Duration**: 0.05s
- **Error**: FileNotFoundError: data/processed/subgraph_with_clusters.parquet not found

### ❌ Run Statistical Analysis
- **Status**: failed
- **Exit Code**: 1
- **Duration**: 0.02s
- **Error**: FileNotFoundError: data/processed/final_analysis_dataset.parquet not found

### ❌ Generate Analysis Report
- **Status**: failed
- **Exit Code**: 1
- **Duration**: 0.01s
- **Error**: FileNotFoundError: artifacts/results/statistical_metrics.json not found

## Artifact Verification

- ❌ `data/processed/subgraph_with_clusters.parquet`
 - **Status**: Missing
- ❌ `data/processed/final_analysis_dataset.parquet`
 - **Status**: Missing
- ❌ `artifacts/results/statistical_metrics.json`
 - **Status**: Missing
- ❌ `artifacts/results/analysis_report.md`
 - **Status**: Missing

## Summary

- **Pipeline Steps Executed**: 5
- **Successful Steps**: 1
- **Failed Steps**: 4
- **Artifacts Present**: 0/4

**Conclusion**: The pipeline validation failed. Review errors above.