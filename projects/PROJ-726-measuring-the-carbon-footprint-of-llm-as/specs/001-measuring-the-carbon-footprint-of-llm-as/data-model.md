# Data Model: Measuring the Carbon Footprint of LLM‑Assisted Code Generation

## Entities

### 1. PromptRecord
Represents a single input prompt from the CodeXGLUE dataset.
- `prompt_id`: string (unique identifier)
- `prompt_text`: string (the actual code generation prompt)
- `source`: string (dataset name, e.g., "codeXglue")

### 2. GenerationRecord
Represents the output of an LLM for a specific prompt.
- `prompt_id`: string (FK to PromptRecord)
- `model_used`: string (e.g., "gpt2-medium", "distilgpt2")
- `generated_code`: string (the code output)
- `loc_count`: integer (lines of code in generated_code, calculated as `len(code.splitlines())`)
- `energy_kWh`: float (measured by CodeCarbon)
- `co2_kg`: float (measured by CodeCarbon)
- `co2_per_loc`: float (calculated: `co2_kg` / `loc_count`)
- `duration_seconds`: float (inference time)
- `region_factor`: float (extracted from CodeCarbon for standardization)

### 3. HumanBaselineRecord
Represents the theoretical human reference energy for a specific prompt.
- `prompt_id`: string (FK to PromptRecord)
- `estimated_human_minutes`: float (from global average or task-specific data)
- `human_energy_kWh`: float (calculated: `minutes` * 15W / 60 / 1000)
- `human_co2_kg`: float (calculated: `human_energy_kWh` * `region_factor` from LLM run)
- `human_loc_count`: integer (Set to `GenerationRecord.loc_count` for common denominator)

### 4. PairedAnalysisRecord
The joined dataset for statistical testing.
- `prompt_id`: string
- `llm_model`: string
- `llm_co2_per_loc`: float
- `human_co2_per_loc`: float
- `difference`: float (`llm_co2_per_loc` - `human_co2_per_loc`)
- `valid`: boolean (true if `loc_count` > 0)

### 5. SensitivityAnalysisRecord
Results of the power model sensitivity check.
- `power_draw_w`: integer (10, 15, 20)
- `human_co2_per_loc`: float
- `difference_from_llm`: float

## Data Flow

1. **Raw Data**: Downloaded parquet files (`data/raw/`).
2. **Validation**: `validate_baseline.py` checks human baseline data for raw time.
3. **Processed Data**: `GenerationRecord` and `HumanBaselineRecord` joined on `prompt_id` (using LLM `loc_count` as common denominator) → `PairedAnalysisRecord` (`data/processed/paired_analysis.csv`).
4. **Results**: Statistical test results (JSON) and plots (PNG) stored in `data/outputs/`.

## Constraints

- **Non-Zero LOC**: Any record with `loc_count` == 0 is excluded from `PairedAnalysisRecord`.
- **Data Integrity**: All derived fields (`co2_per_loc`, `difference`) are calculated programmatically and not stored in raw data.
- **Checksums**: Raw parquet files are checksummed upon download.
- **Common Denominator**: The `loc_count` for the human baseline is set to the LLM's `loc_count` to ensure a valid comparison of "Energy to produce this specific output".