# Data Model: llmXive follow-up: extending "Mellum2 Technical Report"

## Overview
This document defines the data structures used throughout the pipeline, ensuring type safety and reproducibility. All data is stored in Parquet format for efficient streaming and columnar access.

## Entities

### 1. CodeChunk
A segment of source code with associated metadata.
- **id**: `string` (Unique identifier, e.g., `repo:file:chunk_index`)
- **repo_name**: `string` (Source repository)
- **language**: `string` (e.g., "Python", "Java")
- **content**: `string` (Raw source code)
- **cyclomatic_complexity**: `integer` (Static analysis result)
- **nesting_depth**: `integer` (Static analysis result)
- **repetition_ratio**: `float` (Static analysis result)
- **token_count**: `integer` (Length of the code chunk; used as a mandatory confounder control)
- **ngram_probability**: `float` (Estimated by KenLM; used for division-based normalization per FR-010, and as a covariate in robustness checks)
- **per_token_loss**: `float` (LLM inference result)
- **entropy**: `float` (LLM inference result)
- **inference_time_ms**: `integer` (Timing metric)
- **status**: `string` ("success", "timeout", "parse_error")

### 2. RepositoryAggregate
Aggregated metrics for a single repository (used for permutation testing).
- **repo_name**: `string`
- **language**: `string`
- **mean_cyclomatic_complexity**: `float`
- **mean_nesting_depth**: `float`
- **mean_per_token_loss**: `float`
- **mean_ngram_probability**: `float`
- **mean_token_count**: `float`
- **chunk_count**: `integer`

### 3. CorrelationResult
Statistical output for a specific metric pair.
- **metric_name**: `string` (e.g., "cyclomatic_complexity")
- **correlation_coefficient**: `float` (Pearson/Spearman)
- **p_value**: `float` (Raw p-value)
- **p_value_adjusted**: `float` (FDR corrected)
- **sample_size**: `integer` (Number of repositories)
- **method**: `string` ("pearson", "spearman")

### 4. ThresholdResult
Output from change-point detection.
- **metric_name**: `string`
- **threshold_value**: `float` (The identified breakpoint)
- **slope_before**: `float`
- **slope_after**: `float`
- **aic_score**: `float` (Model fit metric)
- **bics_score**: `float`
- **significance**: `boolean` (Is non-linear fit preferred?)
- **bootstrap_stability**: `float` (Max shift across bootstrap samples)
- **confidence_interval_width**: `float` (Width of 95% CI; used to validate stability)

## Data Flow

1.  **Raw Ingestion**: `codeparrot/github-code` (Parquet) -> `CodeChunk` (filtered).
2.  **Static Analysis**: `CodeChunk` -> `CodeChunk` (enriched with complexity metrics).
3.  **Baseline Modeling**: Build KenLM model (Phase 3).
4.  **Inference**: `CodeChunk` -> `CodeChunk` (enriched with loss/entropy).
5.  **Aggregation**: `CodeChunk` (filtered by status="success") -> **`RepositoryAggregate`** (mean per repo).
6.  **Analysis**: `RepositoryAggregate` -> `CorrelationResult` / `ThresholdResult`.
7.  **Output**: Results written to `data/results/` as Parquet and JSON.

## Storage Constraints
- **Raw Data**: Not stored permanently; processed via stream.
- **Processed Data**: Stored in `data/processed/` with checksums.
- **Max Size**: < 14 GB (runner disk limit).
- **Compression**: Parquet (snappy) used for all intermediate and final artifacts.

## Aggregation Strategy
To address the hierarchical nature of the data (chunks within repos), all statistical tests (correlation, permutation) are performed on **repository-level aggregates** (mean metrics per repo). This ensures the unit of analysis matches the unit of permutation, preventing inflated Type I error rates.