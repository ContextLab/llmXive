# Data Model: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Overview
The data model captures every artifact from raw ingestion through final analysis, ensuring traceability, reproducibility, and compliance with the project's constitution and contract schemas.

## Entity‑Relationship Summary
```
[Scenario] 1---N [Stimulus Variant] N---M [Response]
      |                                 |
      |                                 v
      +--------------------> [Participant]
```

## Schemas (refer to `contracts/`)

### Scenario (derived from `contracts/dataset.schema.yaml`)
- `scenario_id` (string)  
- `original_image_path` (string)  
- `metadata` (object) – includes tags, object list, etc.  
- `ambiguity_score` (float) – mean human coding rating (1‑5).  
- `ambiguity_label` (boolean) – retained if mean ≥ 3.5 & κ ≥ 0.6.  

### Stimulus Variant (see `contracts/stimulus.schema.yaml`)
- `variant_id` (string)  
- `scenario_id` (FK)  
- `salience_level` (`low`/`medium`/`high`)  
- `manipulation_params` (contrast, brightness, version)  
- `clip_similarity` (float ≥ 0.95)  
- `rms_contrast_change` (float ≥ 15)  
- `moral_intent_preservation_score` (float ≥ 0.90)  
- `semantic_integrity` (`passed`/`failed`)  
- `image_path` (string)  

### Participant (see `contracts/participant.schema.yaml`)
- `participant_id` (string)  
- `start_time`, `end_time` (ISO‑8601)  
- `total_responses` (int)  
- `exclusion_flag` (bool)  
- `exclusion_reason` (optional string)  

### Response (see `contracts/response.schema.yaml`)
- `response_id` (string)  
- `participant_id` (FK)  
- `variant_id` (FK)  
- `blame_rating` (int 1‑7)  
- `timestamp` (ISO‑8601)  
- `valid` (bool) – set by cleaning step  

### Analysis Output (see `contracts/analysis_schema.yaml`)
- `analysis_id`, `model_type`, `fixed_effects`, `random_effects_variance`, `p_value`, `p_value_corrected`, `effect_size` (odds ratio + CI), `post_hoc_tests`, `exclusion_rate`, `sample_size`, `convergence_status`, `fallback_method`, `wilcoxon_results`, `power_analysis` (observed power, flags, CI‑width check).  

## Data Flow
1. **Ingestion & Filtering** (`01_ingest_and_filter.py`) → `data/raw/` (Open Images V6 streaming) → `candidates_filtered.csv`.  
2. **Human Coding** (`04_human_coding.py`) → `scenarios.csv`.  
3. **Manipulation** (`03_manipulate_stimuli.py`) → `stimuli_manifest.csv` + image files under `data/processed/stimuli/`.  
4. **Survey** (`04_survey_deployment.py`) → `responses_raw.csv`.  
5. **Cleaning** (`05_data_cleaning.py`) → `responses_cleaned.csv` + `participants_excluded.csv`.  
6. **Analysis** (`06_analysis_clmm.py`) → `analysis_results.json`.  

All files are listed in `data/checksums.txt` for integrity verification (Principle III). No file is modified in place; each transformation writes a new artifact with a derivation log.

## Constraints
- No in‑place modification; every step produces a new file.  
- All numeric thresholds (CLIP ≥ 0.95, RMS contrast ≥ 15 %, moral‑intent ≥ 0.90, κ ≥ 0.6, etc.) are enforced programmatically and validated against their respective contract schemas.  
- Participant IDs are anonymized via a hash of the raw platform ID.  

## Contract Coverage
- **Dataset schema** (`contracts/dataset.schema.yaml`) validates `scenarios.csv`.  
- **Participant schema** (`contracts/participant.schema.yaml`) validates `participants_excluded.csv`.  
- **Stimuli manifest schema** (`contracts/stimuli_manifest.schema.yaml`) validates `stimuli_manifest.csv`.  
- **Response schema** (`contracts/response.schema.yaml`) validates both raw and cleaned response files.  
- **Stimulus schema** (`contracts/stimulus.schema.yaml`) validates each manipulated image file entry.  

---

