# Pipeline Implementation Guide

This document details the architecture, execution flow, and data contracts of the llmXive research pipeline.

## Architecture Overview

The pipeline is designed as a Directed Acyclic Graph (DAG) of tasks, orchestrated by `src/orchestration/orchestrator.py`. It is divided into distinct phases:

1. **Setup**: Environment validation, model selection, and configuration.
2. **Data Ingestion**: Fetching real-world vulnerability datasets.
3. **Preprocessing**: Parsing, cleaning, and stratified sampling.
4. **Feature Engineering**: Extracting structural, semantic, and embedding features.
5. **Inference**: Zero-shot LLM classification and static analysis baselines.
6. **Analysis**: Statistical testing, regression, and visualization.
7. **Reporting**: Generating final research artifacts.

## Execution Flow

### 1. Pre-Flight Checks
- **CPU Check (`T004b`)**: Ensures no GPU is present. If `torch.cuda.is_available()` is True, the pipeline aborts.
- **Model Selection (`T004a`)**: Iterates through a candidate list of LLMs to find the first one that performs inference within time limits on CPU.
- **Batch Sizing (`T004d`)**: Calculates optimal batch size based on available RAM and model memory footprint.

### 2. Data Ingestion (Phase 3)
- **Strict Loading**: `src/data/ingest.py` implements `fetch_real_data()` which raises `RuntimeError` on network failure. No synthetic fallbacks are permitted.
- **Datasets**:
 - `VulDeePecker` (Python)
 - `JSVulnDB` (JavaScript)
 - `NIST Juliet` (C/C++)
- **Output**: Unified `CodeSnippet` parquet files in `data/processed/`.

### 3. Feature Extraction (Phase 4)
- **Structural**: AST depth, node count (via `tree-sitter`), cyclomatic complexity (via `radon`).
- **Semantic**: Taint-source API counts, sanitization function counts.
- **Embeddings**: Sentence-transformer embeddings for similarity scoring against NVD reference patterns.
- **Output**: `data/processed/features.csv` adhering to `FeatureVector` schema.

### 4. Inference (Phase 3 & 5)
- **LLM Inference**: Zero-shot prompting with context truncation handling.
- **Static Analysis**: Wrapper for Bandit (Python) and Cppcheck (C).
- **Output**: `data/results/llm_predictions_raw.json`, `data/processed/static_predictions.csv`.

### 5. Analysis (Phase 6)
- **Metrics**: Precision, Recall, F1 per category.
- **Regression**: Logistic regression to identify feature importance.
- **Sensitivity**: Independent re-labeling protocol using secondary datasets.
- **Output**: `data/results/metrics.json`, `research.md`.

## Data Contracts

All data artifacts must adhere to Pydantic schemas defined in `contracts/`:

- **CodeSnippet**: `code`, `language`, `ground_truth_label`, `cwe_category`
- **FeatureVector**: `structural_features`, `semantic_features`, `embedding_similarity_score`
- **PredictionResult**: `model`, `prediction`, `confidence`, `inference_time_ms`
- **AnalysisMetric**: `precision`, `recall`, `f1`, `roc_auc`

## Logging & State

- **Structured Logging**: All events logged to `data/logs/` in JSON format via `src/utils/logger.py`.
- **State Tracking**: Pipeline status and artifact hashes updated in `state/projects/`.
- **Verification**: Critical steps (e.g., stratification, independence checks) produce explicit pass/fail logs.

## Troubleshooting

- **GPU Detected**: The pipeline is CPU-only. Remove CUDA or set `CUDA_VISIBLE_DEVICES=""`.
- **Memory Errors**: Check `data/logs/memory_monitor.json` for peak usage. Reduce batch size in `config.py`.
- **Data Fetch Failures**: Ensure network access to Hugging Face and NVD. The pipeline will abort, not substitute data.
- **Schema Violations**: Verify input data matches `contracts/*.yaml` definitions.
