# Data Model: llmXive Overfitting Trajectory Study

## Overview

This document defines the data structures, schemas, and storage formats for the llmXive follow-up study. All data is stored in the `data/` directory of the project.

## Entities

### 1. Micro-Corpus (Raw & Processed)

**Description**: The curated dataset of M tokens.
**Source**: Project Gutenberg + The Stack.
**Format**: JSONL (one tokenized sequence per line).

**Fields**:
- `id`: Unique string identifier (hash of content).
- `text`: Original text (optional, for debugging).
- `input_ids`: List of integers (token IDs).
- `attention_mask`: List of integers.
- `source`: String ("gutenberg" or "the-stack").

**Storage Path**: `data/processed/micro_corpus_train.jsonl`, `data/processed/micro_corpus_test.jsonl`.

### 2. Training Log

**Description**: Time-series record of model performance and resource usage.
**Format**: CSV.

**Fields**:
- `run_id`: String (UUID).
- `model_type`: String ("autoregressive" or "diffusion").
- `seed_id`: Integer (0-4, representing the 5 seeds).
- `epoch`: Integer (1-100).
- `train_loss`: Float.
- `val_loss`: Float.
- `generalization_gap`: Float (train_loss - val_loss).
- `perplexity`: Float (exp(val_loss)).
- `wall_clock_time_sec`: Float (cumulative time).
- `ram_usage_gb`: Float (peak RAM during epoch).
- `timestamp`: ISO 8601 datetime.

**Storage Path**: `data/artifacts/training_logs.csv`.

### 3. Statistical Results

**Description**: Output of the ANOVA and correlation analysis.
**Format**: JSON.

**Fields**:
- `anova_table`: Object (source, df, sum_sq, mean_sq, f, p).
- `interaction_p_value`: Float.
- `interaction_effect_size`: Float (partial eta-squared).
- `gap_slope_ar`: Float (slope of AR gap).
- `gap_slope_diffusion`: Float (slope of Diffusion gap).
- `correlation_r_ar`: Float.
- `correlation_r_diffusion`: Float.
- `correlation_p_ar`: Float.
- `correlation_p_diffusion`: Float.
- `epochs_completed`: Integer.
- `power_analysis`: Object (effect_size, power, n_epochs).
- `a_priori_power_analysis`: Object (target_power, assumed_effect_size, calculated_power).
- `cross_domain_metrics`: Object (wikitext_perplexity_ar, wikitext_perplexity_diffusion).

**Storage Path**: `data/artifacts/statistical_results.json`.

### 4. HumanEval Results

**Description**: Performance on the HumanEval benchmark.
**Format**: JSON.

**Fields**:
- `model_type`: String.
- `seed_id`: Integer.
- `pass@1`: Float.
- `pass@10`: Float.
- `perplexity`: Float.

**Storage Path**: `data/artifacts/human_eval_results.json`.

### 5. Corpus Validation Report

**Description**: Verification of token count and HumanEval exclusion.
**Format**: JSON.

**Fields**:
- `token_count`: Integer.
- `status`: String ("PASS" or "FAIL").
- `human_eval_excluded`: Boolean.
- `checksum_sha256`: String.

**Storage Path**: `data/artifacts/corpus_validation.json`.

## Data Flow

1.  **Download**: Raw text fetched from Hugging Face -> `data/raw/`.
2.  **Tokenize**: `gpt2` tokenizer applied -> `data/processed/`.
3.  **Validate**: Check token count and exclusion -> `data/artifacts/corpus_validation.json`.
4.  **Train**: Models iterate over `data/processed/` -> `data/artifacts/training_logs.csv`.
5.  **Evaluate**: HumanEval on checkpoints -> `data/artifacts/human_eval_results.json`.
6.  **Analyze**: Script reads logs and results -> `data/artifacts/statistical_results.json`.

## Constraints

- **Token Count**: Must be within a specific large magnitude range.
- **No Overlap**: Train and Test sets must have zero sequence overlap.
- **Checksum**: All processed files must be checksummed (SHA-256).
- **Seeds**: A small number of seeds per architecture (depending on feasibility).
