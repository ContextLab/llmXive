# Data Model: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Overview

This document defines the data structures, schemas, and relationships used throughout the project. All data artifacts are stored in `data/` and validated against the schemas in `contracts/`.

## Entity Definitions

### 1. Prompt
A text input from the CodeXGLUE dataset.
- **Attributes**:
  - `prompt_id`: Unique identifier (string).
  - `text`: The raw prompt text (string).
  - `source`: Dataset name (string, e.g., "code_x_glue").

### 2. Generation
The code output produced by an LLM.
- **Attributes**:
  - `prompt_id`: Foreign key to Prompt.
  - `model_id`: Identifier of the model used (e.g., "gpt2-medium").
  - `generated_code`: The generated code string.
  - `loc_count`: Number of lines of code (integer).
  - `success`: Boolean indicating if generation was valid.

### 3. EmissionRecord
A record of energy consumption and emissions for a single inference.
- **Attributes**:
  - `prompt_id`: Foreign key to Prompt.
  - `model_id`: Identifier of the model used.
  - `energy_kWh`: Energy consumed (float).
  - `co2_kg`: CO₂ equivalent emitted (float).
  - `device`: Device used (e.g., "cpu").
  - `region_factor`: The regional emission factor used (float).

### 4. HumanBaseline
Static data mapping prompts to estimated human development time.
- **Attributes**:
  - `prompt_id`: Foreign key to Prompt.
  - `time_minutes`: Estimated time in minutes (float).
  - `source`: Citation of the literature used for synthesis (string).

### 5. PairedEmission
The joined dataset for statistical analysis.
- **Attributes**:
  - `prompt_id`: Primary key.
  - `llm_co2_per_loc`: Emissions per LOC for LLM (float).
  - `human_co2_per_loc`: Emissions per LOC for Human (float).
  - `diff`: Difference (LLM - Human) (float).
  - `valid`: Boolean (true if both LOC > 0).

### 6. StatisticalResult
The output of the statistical test.
- **Attributes**:
  - `test_type`: "overlap_analysis" or "t-test".
  - `statistic`: Test statistic value (float).
  - `p_value`: P-value (float).
  - `effect_size`: Cohen's d or rank-biserial (float).
  - `ci_lower`: Lower bound of 95% CI for mean difference (float).
  - `ci_upper`: Upper bound of 95% CI for mean difference (float).
  - `shapiro_p`: P-value from normality test (float).
  - `model_id`: Which model this result applies to.
  - `overlap_status`: "overlap" or "no_overlap" (for overlap analysis).

## Data Flow

1. **Download**: `Prompt` data is fetched and stored in `data/raw/prompts.json`.
2. **Inference**: `Generation` and `EmissionRecord` data are generated and stored in `data/processed/inference_results.json`.
3. **Baseline**: `HumanBaseline` data is loaded from `data/raw/human_baseline_times.json`.
4. **Normalization**: `PairedEmission` data is created in `data/processed/paired_emissions.csv`.
5. **Sensitivity**: `sensitivity_analysis.csv` is created with Low/Med/High power draw scenarios.
6. **Analysis**: `StatisticalResult` is computed and stored in `data/outputs/stats_summary.json`.
7. **Report**: Final report is generated in `data/outputs/report.md`.

## File Formats

- **JSON**: Used for structured records (prompts, inference results, stats).
- **CSV**: Used for paired emissions and sensitivity analysis for easy inspection and plotting.
- **Markdown**: Used for the final report.