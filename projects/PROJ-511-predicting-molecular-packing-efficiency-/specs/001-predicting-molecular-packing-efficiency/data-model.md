# Data Model: Predicting Molecular Packing Efficiency

## Overview
Schemas define the structure of all data artifacts exchanged between pipeline stages. Validation against these JSON‑Schema contracts guarantees reproducibility and enables automated testing.

## Entity Relationships
1. **Raw COD download** → **Filtered Record** (JSONL)  
2. **Filtered Record** → **SMILES & 3‑D Descriptors** (CSV)  
3. **SMILES & 3‑D Descriptors** → **Embedding Generation** (CSV with `fingerprint_vector`)  
4. **Feature Matrix** → **Trained Models** (PyTorch checkpoints)  
5. **Model Predictions + Ground Truth** → **Validation Report** (JSON)  
6. **Validation Report** → **HTML Report** (final deliverable)  

## Schemas

### 1. Full Feature Matrix (`data/processed/full_feature_matrix.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `cod_id` | string | Unique COD identifier (provenance). |
| `smiles` | string | Canonical SMILES (extracted or generated). |
| `smiles_source` | string (`"extracted"` | `"generated"`) | Origin of SMILES. |
| `unit_cell_volume` | number | Unit‑cell volume (Å³). |
| `pc_raw` | number | **Primary target** – raw packing coefficient. |
| `radius_of_gyration` | number | 3‑D descriptor (Å). |
| `asphericity` | number | 3‑D descriptor (0–1). |
| `principal_moments` | string (JSON) | `[I1, I2, I3]` in Å⁴. |
| `lattice_system` | string | Crystal system (e.g., `monoclinic`). |
| `temperature_K` | number | null | Measurement temperature (K). |
| `has_solvent` | boolean | Presence of solvent molecules. |
| `atom_count` | integer | Non‑hydrogen atom count (excluded from Primary Model). |
| `atom_type_counts` | string (JSON) | `{"C":10,"O":2,…}` (excluded from Primary Model). |
| `fingerprint_vector` | string | Space‑separated float list (SMILES‑Transformer embedding). |

**Required fields**: all except `temperature_K` (may be null).  

### 2. Model Checkpoint Metadata (`data/artifacts/model_*.pt` + JSON side‑car)
*Validated by `contracts/model.schema.yaml`.* Includes model type, layer sizes, total parameters, target variable, training config (seed, learning rate, batch size, epochs, train‑split ratio), and creation timestamp.

### 3. Validation Report (`data/artifacts/validation_report.json`)
*Validated by `contracts/validation_report.schema.yaml`.* Contains MAE, Spearman ρ, Pearson r, Shapiro‑Wilk statistics, permutation‑test results (including actual shuffles if timeout), Bonferroni correction details, VIF diagnostics, sensitivity‑analysis table, residual‑composition correlation, and target‑distribution diagnostics.

## Transformation Logic
1. **PC_raw** = `unit_cell_volume / sum(vdw_volume_i)` (FR‑003).  
2. **SMILES Generation**: If `_chemical_structure_SMILES` missing, RDKit builds a Mol from CIF geometry and generates a canonical SMILES (`MolToSmiles(..., isomericSmiles=True)`). Flagged as `"generated"` (FR‑002).  
3. **3‑D Descriptors**: Radius of gyration, asphericity, principal moments computed from atomic coordinates (FR‑012).  
4. **Embedding**: Frozen SMILES‑Transformer applied in streaming batches (batch = 64) → `fingerprint_vector` (FR‑004, FR‑020).  
5. **Feature Matrix Assembly**: Merge all columns; exclude `atom_count` and `atom_type_counts` from the predictor set for the Primary Model (FR‑021).  

## Constraints
- **Atom‑Count Filter**: Drop records with `atom_count` > 50 (FR‑001).  
- **Volume Sanity**: Exclude rows where `unit_cell_volume` < 10 Å³ or > 100 000 Å³.  
- **PC_raw Bounds**: Flag rows where `pc_raw` < 0 or > 10 as erroneous.  
- **Schema Validation**: Executed in Phase 1; any violation aborts the pipeline (Principle III).  

---
