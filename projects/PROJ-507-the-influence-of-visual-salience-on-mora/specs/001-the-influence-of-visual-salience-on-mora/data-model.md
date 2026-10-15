# Data Model: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Overview
The data model captures every artifact from raw ingestion to final analysis, ensuring alignment with the specification, the constitution, and the contract schemas. The primary source of visual material is the **Visual Genome** dataset, which provides everyday scenes with object annotations suitable for moral‑ambiguity selection.

## Entity‑Relationship Summary
```
[Scenario] 1---N [Stimulus Variant] N---M [Response]
      |                                 |
      |                                 v
      +--------------------> [Participant]
```

## Schemas (refer to `contracts/`)

### Scenario (derived from `contracts/dataset.schema.yaml`)
- `scenario_id` (string, e.g., `SCN_001`)  
- `original_image_path` (string)  
- `metadata` (object) – includes tags from Visual Genome objects  
- `ambiguity_score` (float) – mean human coding rating  
- `ambiguity_label` (boolean) – retained if ≥ 3.5 & κ ≥ 0.6  

### Stimulus Variant (see `contracts/stimulus.schema.yaml`)
- `variant_id` (string, e.g., `STI_001_low`)  
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
- `exclusion_reason` (string, optional)  

### Response (see `contracts/response.schema.yaml`)
- `response_id` (string)  
- `participant_id` (FK)  
- `variant_id` (FK)  
- `blame_rating` (int 1‑7)  
- `timestamp` (ISO‑8601)  
- `valid` (bool) – set by cleaning step  

### Analysis Output (see `contracts/analysis_schema.yaml`)
- `analysis_id`, `model_type`, `fixed_effects`, `random_effects_variance`, `p_value`, `p_value_corrected`, `effect_size`, `post_hoc_tests`, `exclusion_rate`, `sample_size`, `convergence_status`, `fallback_method`, `wilcoxon_results`, `power_analysis`.

## Data Flow
1. **Ingestion** (`01_ingest_and_filter.py`) → `data/raw/clip_metadata.csv` (Visual Genome metadata).  
2. **Filtering & Human Coding** → `data/processed/scenarios.csv`.  
3. **Manipulation** → `data/processed/stimuli/` + `stimuli_manifest.csv`.  
4. **Survey** → `data/processed/responses_raw.csv`.  
5. **Cleaning** → `responses_cleaned.csv`.  
6. **Analysis** → `analysis_results.json`.  

All files are checksummed (`data/checksums.txt`) and version‑tracked.

## Constraints
- No in‑place modification of any file.  
- All numeric thresholds (e.g., CLIP ≥ 0.95) are enforced programmatically and validated against the corresponding contract schema.  
- Participant IDs are anonymized (hash of Prolific ID).  

---

