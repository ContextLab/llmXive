# Data Model: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Overview

This document defines the data entities, schemas, and relationships used in the carbon footprint measurement pipeline. All data is stored in JSON/CSV formats to ensure portability and reproducibility.

## Entities

### 1. Prompt
A text input from the CodeXGLUE dataset.
- **Fields**: `prompt_id` (str), `text` (str), `source` (str).

### 2. Generation
The code output produced by the LLM.
- **Fields**: `generation_id` (str), `prompt_id` (str), `model_used` (str), `generated_code` (str), `status` (str: "success" | "failed").

### 3. EmissionRecord
The core entity containing energy and emission metrics.
- **Fields**: `record_id` (str), `prompt_id` (str), `model_used` (str), `energy_kWh` (float), `co2_kg` (float), `loc_count` (int), `co2_per_loc` (float).

### 4. HumanBaseline
A static configuration representing the human developer's carbon footprint.
- **Fields**: `baseline_id` (str), `estimated_time_minutes` (float), `power_draw_w` (float), `emission_factor` (float), `co2_kg` (float), `co2_per_loc` (float).

### 5. AnalysisResult
The output of the statistical comparison.
- **Fields**: `analysis_id` (str), `model_used` (str), `llm_mean_co2` (float), `human_co2` (float), `overlap_percentage` (float), `direction` (str: "higher" | "lower" | "mixed"), `sensitivity_range` (dict).

## Data Flow

1. **Raw Data**: `data/raw/codexglue_sample.json` (Prompts)
2. **Inference Output**: `data/processed/llm_inference_results.json` (Generations + Energy)
3. **Normalized Data**: `data/processed/emissions_per_loc.csv` (Combined LLM + Human)
4. **Final Analysis**: `data/processed/statistical_analysis.json` (Results)

## Schema Definitions (Contracts)

The following schemas are defined in `contracts/` to validate data integrity.
