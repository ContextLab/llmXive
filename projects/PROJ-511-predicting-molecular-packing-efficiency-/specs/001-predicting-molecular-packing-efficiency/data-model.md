# Data Model: Predicting Molecular Packing Efficiency

## Overview
This document defines the schemas for all data artifacts exchanged between pipeline stages. Validation against the JSON‑Schema contracts ensures reproducibility and automated testing.

## Entity Relationships
1. **Raw CIF download** → **Filtered Record** (JSONL)  
2. **Filtered Record** → **SMILES & 3‑D Descriptors** (CSV)  
3. **SMILES & 3‑D Descriptors** → **Embedding Generation** (CSV with `fingerprint_vector`)  
4. **Feature Matrix** → **Trained Models** (PyTorch checkpoints)  
5. **Model Predictions + Ground Truth** → **Validation Report** (JSON)  
6. **Validation Report** → **HTML Report** (final deliverable)

## Schemas

### 1. Raw COD Download (JSONL)
*Source*: Verified COD loader (`datasets.load_dataset("cod/cod")`).  
Key fields (excerpt):
- `_cod_id` (string) – unique COD identifier  
- `_cell_volume` (float) – unit‑cell volume (Å³)  
- `_symmetry_space_group_name_H-M` (string) – space‑group label  
- `_chemical_structure_SMILES` (string, optional) – deposited SMILES  
- `_exptl_crystal_growth_temperature` (float, optional) – temperature (K)  

### 2. Processed Feature Matrix (`data/processed/full_feature_matrix.csv`)
| Column | Type | Description |
|--------|------|-------------|
| `cod_id` | string | COD identifier (provenance). |
| `smiles` | string | Canonical SMILES (extracted or generated). |
| `smiles_source` | string (`"extracted"` | `"generated"`) | Origin of the SMILES. |
| `unit_cell_volume` | number | Unit‑cell volume (Å³). |
| `pc_raw` | number | **Primary target** – raw packing coefficient. |
| `cape` | number | Composition‑adjusted packing efficiency (diagnostic only). |
| `radius_of_gyration` | number | 3‑D descriptor (Å). |
| `asphericity` | number | 3‑D descriptor (unitless, 0–1). |
| `principal_moments` | string (JSON) | `[I1, I2, I3]` in Å⁴. |
| `lattice_system` | string | Crystal system (e.g., `monoclinic`). |
| `temperature_K` | number | null | Measurement temperature (K). |
| `has_solvent` | boolean | Presence of solvent molecules. |
| `atom_count` | integer | Non‑hydrogen atom count (excluded from primary regression). |
| `atom_type_counts` | string (JSON) | `{"C":10,"O":2,…}` (excluded from primary regression). |
| `fingerprint_vector` | string | Space‑separated float list (embedding). |

**Required fields**: all listed except `temperature_K` which may be null.

### 3. Model Checkpoint (`data/artifacts/model_primary.pt`, `model_full.pt`)
*Binary PyTorch state dict* plus accompanying JSON metadata (validated by `contracts/model.schema.yaml`).

### 4. Validation Report (`data/artifacts/validation_report.json`)
Conforms to `contracts/validation_report.schema.yaml`. Contains MAE, correlation coefficients, Shapiro‑Wilk statistics, permutation‑test results, Bonferroni‑adjusted p‑values, VIF flags, sensitivity‑analysis table, residual‑composition correlation, and target‑distribution diagnostics.

## Transformation Logic
1. **PC_raw**: `unit_cell_volume / sum(vdw_volume_i)` (FR‑003).  
2. **CAPE**: `pc_raw / (mean(vdw_volume_i))` (diagnostic only).  
3. **SMILES Generation**: If `_chemical_structure_SMILES` missing, use RDKit to build a Mol from the CIF geometry and `MolToSmiles(..., isomericSmiles=True)`. Flag as `"generated"`.  
4. **3‑D Descriptors**: Compute radius of gyration, asphericity, principal moments from atomic coordinates (FR‑012).  
5. **Embedding**: Frozen SMILES‑Transformer applied in streaming batches (batch = 64) → `fingerprint_vector`.  
6. **Feature Matrix Assembly**: Merge all columns; exclude `atom_count` and `atom_type_counts` from the predictor set for the Primary Model (FR‑021).  

## Constraints
- **Atom‑Count Filter**: Drop records with `atom_count` > 50 (FR‑001).  
- **Volume Sanity**: Exclude rows where `unit_cell_volume` < 10 Å³ or > 100 000 Å³.  
- **PC_raw Bounds**: Flag rows where `pc_raw` < 0 or > 10 as erroneous.  
- **Schema Validation**: Executed in Phase 1; any violation aborts the pipeline (ensuring data hygiene, Principle III).  

---
