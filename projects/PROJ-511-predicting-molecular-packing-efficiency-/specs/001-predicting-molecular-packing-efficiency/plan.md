# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-predicting-molecular-packing-efficiency`  
**Date**: 2026-10-11  
**Spec**: `spec.md`  
**Input**: Feature specification from `specs/PROJ-511-predicting-molecular-packing-efficiency/spec.md`

## Summary
Build a **CPU‑only** end‑to‑end pipeline that (1) downloads organic crystal entries from the Crystallography Open Database (COD), (2) extracts or generates canonical SMILES, (3) computes the packing coefficient (PC) and 3‑D geometry descriptors, (4) encodes SMILES with a frozen transformer (streaming inference), (5) trains two lightweight 2‑layer MLP regressors (SMILES‑only *Primary Model* and SMILES + 3‑D *Full Model*), (6) evaluates performance with MAE, Spearman ρ, Pearson’s r, Shapiro‑Wilk, a 10 000‑shuffle permutation test (with timeout‑aware handling), VIF diagnostics (restricted to non‑fingerprint predictors), and a Bonferroni‑corrected sensitivity analysis over high‑packing thresholds {0.5, 0.6, 0.7}, and (7) generates a reproducible HTML report that validates against `contracts/validation_report.schema.yaml`.

All steps must complete on a GitHub Actions free‑tier runner (2 CPU cores, ~7 GB RAM, ≤6 h). A GPU escape hatch is prepared for transformer inference if OOM occurs.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `rdkit`, `torch` (CPU‑only), `transformers`, `scikit-learn`, `pandas`, `numpy`, `joblib`, `datasets`, `jinja2`, `pyyaml`, `scipy`, `statsmodels`  
- **Storage**: Local `data/` hierarchy (raw, processed, artifacts)  
- **Testing**: `pytest` (unit + integration)  
- **Target Platform**: Linux CI runner (GitHub Actions)  
- **Performance Goals**: End‑to‑end ≤ 6 h, model training ≤ 30 min, permutation test ≤ 2 h (fallback)  
- **Constraints**: CPU‑first; GPU only as automatic Kaggle escape hatch; streaming inference to stay < 7 GB RAM  
- **Scale/Scope**: Minimum 500 valid records after filtering; ≤ 100 k trainable parameters per model  

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All random seeds (`numpy`, `torch`, `random`) are pinned in `code/utils/random.py`. External datasets are fetched deterministically from the same source on every run. |
| **II. Verified Accuracy** | Citations for Bondi radii (FR‑017) are recorded. **COD provenance (FR‑016) currently lacks a verified download URL; this violates Principle VI.** The plan flags this as a blocking issue and proposes to supply a verified COD mirror or adopt an open substitute before any Phase 0 work runs. |
| **III. Data Hygiene** | Raw downloads are stored unchanged under `data/raw/`. Every derived file is checksum‑verified (SHA‑256) and accompanied by a provenance JSON. |
| **IV. Single Source of Truth** | Every figure, table, and statistic in `report.html` is generated programmatically from validated CSVs; no hand‑typed numbers. |
| **V. Versioning Discipline** | Content hashes for all artifacts are recorded in `state/projects/PROJ-511-predicting-molecular-packing-efficiency-.yaml`. |
| **VI. Open Crystallographic Data Integrity** | The pipeline **requires** COD entries. **No verified COD URL is present in the “Verified datasets” block**, constituting a current violation. This must be resolved (provide a verified COD mirror or use an open substitute) before execution. |
| **VII. Model Transparency and Statistical Validation** | Model architecture, hyper‑parameters, and training script are committed. Permutation test uses a sufficiently large number of shuffles (or a documented fallback). All diagnostics are included in the validation report. |

## Project Structure
```text
projects/PROJ-511-predicting-molecular-packing-efficiency-/
├── code/
│   ├── __init__.py
│   ├── utils/
│   │   ├── random.py               # Seed management
│   │   ├── rdkit_helpers.py        # SMILES extraction/generation, 3‑D descriptors
│   │   └── stats.py                # VIF, permutation test, Shapiro‑Wilk
│   ├── download_cod.py             # FR‑001, FR‑011
│   ├── generate_smiles.py          # FR‑002
│   ├── compute_descriptors.py      # FR‑012, FR‑021
│   ├── encode_smiles.py            # FR‑004 (streaming transformer)
│   ├── train_model.py              # FR‑005
│   ├── evaluate_model.py           # FR‑006, FR‑009, FR‑014, FR‑015
│   ├── sensitivity_analysis.py    # FR‑007, FR‑008
│   ├── report_generator.py         # FR‑010
│   └── requirements.txt
├── data/
│   ├── raw/                         # Unmodified COD downloads
│   ├── processed/                   # CSVs, feature matrix
│   └── artifacts/                   # Model checkpoints, reports, logs
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model.schema.yaml
│   └── validation_report.schema.yaml
└── tests/
    ├── unit/
    └── integration/
```

## Phase Execution Order & FR Mapping
| Phase | Description | Script(s) | FR(s) Covered |
|-------|-------------|-----------|----------------|
| **Phase 0 – Data Acquisition & Feature Engineering** | Download COD, filter organic ≤ 50 non‑hydrogen atoms, extract/generate SMILES, compute PC, 3‑D descriptors, encode SMILES, add confounder counts, merge into full feature matrix. **Also computes the Packing Coefficient (FR‑011).** | `download_cod.py`, `generate_smiles.py`, `compute_descriptors.py`, `encode_smiles.py`, `generate_confounders.py` | FR‑001, FR‑002, FR‑003, FR‑004, FR‑011, FR‑012, FR‑017, FR‑019, FR‑020, FR‑021 |
| **Phase 1 – Data Validation & Diagnostics** | Schema validation against `contracts/dataset.schema.yaml`, checksum logging, VIF diagnostics **restricted to non‑fingerprint predictors or PCA‑reduced fingerprint (≤20 components)**, target‑distribution normality check, power analysis (bootstrap) (FR‑009, FR‑014, FR‑016, FR‑017, FR‑019). | `evaluate_model.py` (validation sub‑routines) | FR‑009, FR‑014, FR‑016, FR‑017, FR‑019 |
| **Phase 2 – Model Training** | Train Primary (SMILES‑only) and Full (SMILES + 3‑D) 2‑layer MLPs on an 80/20 split. | `train_model.py` | FR‑005 |
| **Phase 3 – Evaluation & Robustness** | Compute MAE, Spearman ρ, Pearson r **only if the pair (predicted, observed PC) passes a bivariate normality check** (joint Shapiro‑Wilk), Shapiro‑Wilk on residuals, permutation test (10 000 shuffles, timeout‑aware: if the 2‑h hard limit is hit we report the p‑value based on the actual shuffles performed together with a Wilson‑score confidence interval), Bonferroni‑corrected p‑values, residual‑composition correlation, Feature Ablation (compare Primary vs Full). **Explicitly enforce SC‑002 (Spearman ρ ≥ 0.3 and Bonferroni‑corrected p ≤ 0.05) and SC‑003 (if ρ < 0.2 then p ≥ 0.05) as conditional success criteria.** | `evaluate_model.py` | FR‑006, FR‑008, FR‑010, FR‑013, FR‑014, FR‑015 |
| **Phase 4 – Sensitivity Analysis** | Sweep high‑packing thresholds {0.5, 0.6, 0.7}, compute metrics, apply Bonferroni correction. | `sensitivity_analysis.py` | FR‑007, FR‑008 |
| **Phase 5 – Reporting** | Assemble HTML report, embed provenance, model hashes, and validation JSON. | `report_generator.py` | FR‑010, FR‑018, FR‑020 (streaming inference sanity check) |

All **Success Criteria (SC‑001 – SC‑006)** are verified in the final validation report and the HTML report.

## Compute Feasibility & Data Strategy
1. **CPU‑First**  
   - SMILES‑Transformer inference runs on `device="cpu"` with batch size 64; embeddings streamed to disk in JSONL chunks to keep RAM ≤ 6 GB.  
   - MLP training uses PyTorch CPU tensors; total training time ≤ 30 min on 2 cores.  
   - Permutation test parallelized via `joblib.Parallel(n_jobs=-1)` with a hard timeout of **2 h**; if the timeout fires, the actual number of shuffles performed is recorded and the p‑value is reported together with a Wilson‑score confidence interval, and the deviation is logged (addressing SC‑006).  

2. **GPU Escape Hatch**  
   - If transformer inference OOMs, the same script will automatically re‑run on a Kaggle free GPU (`device="cuda"`), using 8‑bit quantization (`bitsandbytes`) if needed. This satisfies the “real GPU” requirement; no CPU approximation is fabricated.  

3. **Data Availability**  
   - **Verified COD source**: *None* appears in the verified‑datasets block, so the pipeline cannot automatically fetch COD on CI. This is a **blocking issue** (Principle VI).  
   - **Proposed resolution**:  
     - **Option A** – Provide a verified COD mirror URL (e.g., a HuggingFace dataset containing the raw CIF files).  
     - **Option B** – Revise the research question to use an openly available crystallographic dataset that includes the required metadata (e.g., a subset of the Materials Project that is publicly downloadable).  
   - Until a verified source is supplied, Phases 0‑5 remain **pending**. The plan explicitly documents this gap to avoid hidden assumptions.  

## Risk Mitigation
| Risk | Mitigation |
|------|------------|
| Missing verified COD data (Principle VI) | Flag as blocking; request a verified COD mirror or adopt an open substitute before any code runs. |
| OOM during `encode_smiles.py` | Streaming inference with batch = 64; automatic Kaggle GPU escape hatch. |
| Permutation test exceeds timeout | Hard 2 h limit; report actual shuffles with confidence interval (SC‑006). |
| Insufficient records after filtering | Abort with clear warning if `< 500` records remain; power analysis (FR‑019) will have already flagged low power. |
| Collinearity among fingerprint dimensions | Compute VIF only on non‑fingerprint predictors or on a PCA‑reduced fingerprint (≤ 20 components); flag high VIF features but retain for reproducibility. |
| Non‑normal residuals | Use Spearman ρ as primary metric; report Pearson r only if the pair (predicted, observed) passes joint normality test; otherwise, rely on Spearman. |
| Multiple‑comparison inflation | Apply Bonferroni correction to the three threshold tests (α_adj ≈ 0.0167) (FR‑008). |
| Data‑hygiene violations | Schema validation (Phase 1) aborts on any missing required column; checksums recorded for all files (Principle III). |

---



## projects/PROJ-511-predicting-molecular-packing-efficiency-/specs/001-predicting-molecular-packing-efficiency/research.md
# Research: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

## Scientific Rationale
The central hypothesis is that **molecular topology**, encoded as canonical SMILES strings, carries predictive information about a crystal’s **raw packing coefficient (PC_raw)**. SMILES captures 2‑D connectivity without explicit 3‑D geometry, so we compare a **SMILES‑only** regression model (Primary Model) against a **Full Model** that also receives geometry‑derived descriptors (radius of gyration, asphericity, principal moments). Demonstrating a statistically significant correlation for the Primary Model would support the claim that topology alone contributes to packing efficiency.

The target variable is defined as  

\[
\text{PC}_{\text{raw}} = \frac{\displaystyle\sum_{i}{V_{\text{vdW},i}}}{\text{Unit‑cell volume}}
\]

using Bondi van der Waals volumes (FR‑017). Atom‑type count features are **excluded** from the Primary Model (FR‑021) and examined only in post‑hoc residual analysis (FR‑014).

A **Geometry‑Only** baseline quantifies the maximal predictive power achievable from crystal coordinates, providing a reference for the incremental contribution of SMILES embeddings.

## Dataset Strategy
| Dataset | Purpose | Verified URL / Loader | Notes |
|---------|---------|-----------------------|-------|
| **COD (Crystallography Open Database)** | Source of CIFs, unit‑cell volumes, lattice metadata, solvent flags, and optional SMILES tags | *No verified URL is present in the “Verified datasets” block.* | Required for FR‑001‑FR‑003. Because no verified download link exists, the pipeline cannot currently fetch COD on CI. This is a **Principle VI violation** that must be resolved (see Plan). |
| **SMILES‑Transformer weights** | Frozen encoder for SMILES strings (FR‑004) | Downloaded automatically via the `transformers` library from HuggingFace (weights cached locally) | CPU‑compatible; streaming inference enforced (FR‑020). |
| **Bondi radii constants** | Atomic vdW volumes for PC calculation (FR‑017) | Implemented via `rdkit.Chem.rdMolDescriptors.GetAtomicVdWVolume` (no external URL) | Cited in FR‑017; satisfies Principle II. |

**Variable Fit Verification**  
Before any analysis, the pipeline validates that each record contains:

- `unit_cell_volume` (mandatory) – abort if missing.  
- `smiles` (extracted or generated) – generated when `_chemical_structure_SMILES` absent (FR‑002).  
- `atom_type_counts` and `atom_count` – used for confounder VIF diagnostics (FR‑012, FR‑021).  

If any mandatory field is absent, the pipeline logs the deficiency and aborts, ensuring data‑hygiene (Principle III).

**Data Volume & Feasibility**  
The COD archive holds > 100 k entries. After filtering for organic molecules with ≤ 50 non‑hydrogen atoms, we anticipate > 500 valid rows (SC‑001). Records are streamed; no full dataset is held in memory. SMILES embeddings are written to disk in batches (≤ 64 per batch) to respect the 7 GB RAM limit.

## Methodological Rigor
| Aspect | Implementation |
|--------|----------------|
| **Multiple‑Comparison Correction** | Bonferroni correction applied to the three high‑packing thresholds (α_adj = 0.05 / 3 ≈ 0.0167) (FR‑008). |
| **Power Justification** | Bootstrap‑based power analysis (FR‑019) on the empirical PC distribution; with N ≥ 500 the power to detect ρ ≥ 0.3 exceeds 90 %. If N < 500, the pipeline aborts and logs a power warning (SC‑001). |
| **Causal Framing** | Observational study; all claims are framed as “predictive association,” not causal inference. |
| **Measurement Validity** | PC_raw uses Bondi radii (FR‑017); SMILES embeddings come from a peer‑reviewed transformer model (citation recorded). |
| **Collinearity & VIF** | VIF diagnostics on the full feature matrix (fingerprint dimensions + 3‑D descriptors + confounders) (FR‑009). Features with VIF > 5 are flagged but retained for reproducibility. |
| **Permutation Test** | Two‑sided permutation test with 10 000 shuffles (FR‑015), parallelized via `joblib`. A hard timeout of 2 h; if exceeded, the actual number of shuffles performed is recorded and the deviation logged (SC‑006). |
| **Residual Analysis** | Correlate model residuals with atom‑type composition to quantify unexplained compositional effects (FR‑014, FR‑021). |
| **Normality Checks** | Shapiro‑Wilk test on residuals; Pearson r reported only if p > 0.05 (FR‑014). |
| **Feature Ablation** | Compare Primary vs Full model performance to quantify the contribution of 3‑D descriptors (FR‑013). |
| **Sensitivity Analysis** | Sweep high‑packing thresholds {0.5, 0.6, 0.7}, compute Spearman ρ, MAE, and permutation p‑values; apply Bonferroni correction (FR‑007, FR‑008). |

## Decision Rationale
- **CPU‑first**: All core components (RDKit, PyTorch‑CPU, scikit‑learn) comfortably fit within the CI runner’s resources.  
- **GPU Escape Hatch**: Reserved only for transformer inference if OOM occurs; the pipeline will automatically off‑load to a Kaggle free GPU, preserving methodological integrity.  
- **Dataset Choice**: COD is the only source that provides the required crystallographic metadata. Because a verified download URL is missing, the plan **flags this as a blocking issue** rather than fabricating a source.  
- **Statistical Controls**: Bonferroni correction, VIF, permutation testing, and power analysis collectively address the methodology‑panel checklist for quantitative rigor.  

---



## projects/PROJ-511-predicting-molecular-packing-efficiency-/specs/001-predicting-molecular-packing-efficiency/data-model.md
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
| `asphericity` | number | Asphericity descriptor (0–1). |
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



## projects/PROJ-511-predicting-molecular-packing-efficiency-/specs/001-predicting-molecular-packing-efficiency/quickstart.md
# Quickstart: Predicting Molecular Packing Efficiency

## Prerequisites
* Python 3.11 or newer  
* `pip` (installed with Python)  
* Internet access to download the COD dataset **once a verified URL is supplied** (see Data Availability note below).  

## Installation
```bash
# Navigate to the project root
cd projects/PROJ-511-predicting-molecular-packing-efficiency-

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r code/requirements.txt
```

## Running the Pipeline
> **Important** – The pipeline cannot start until a verified COD dataset URL is provided (see Data Availability section). Once the source is available, the steps below will run end‑to‑end on a fresh GitHub Actions runner.

### Step 1: Data Acquisition & Feature Engineering (Phase 0)
```bash
# 1. Download and filter COD entries (organic ≤ 50 non‑H atoms)
python code/download_cod.py --output data/raw/cod.jsonl

# 2. Extract or generate SMILES
python code/generate_smiles.py \
    --input data/raw/cod.jsonl \
    --output data/processed/with_smiles.csv

# 3. Compute 3‑D geometry descriptors and confounder counts
python code/compute_descriptors.py \
    --input data/processed/with_smiles.csv \
    --output data/processed/with_descriptors.csv

# 4. Encode SMILES with the frozen transformer (streaming)
python code/encode_smiles.py \
    --input data/processed/with_descriptors.csv \
    --output data/processed/full_feature_matrix.csv
```

### Step 2: Model Training (Phase 2)
```bash
python code/train_model.py \
    --data data/processed/full_feature_matrix.csv \
    --model-primary data/artifacts/model_primary.pt \
    --model-full data/artifacts/model_full.pt
```

### Step 3: Evaluation & Reporting (Phases 3‑5)
```bash
# Evaluation (metrics, permutation test, VIF, residual analysis)
python code/evaluate_model.py \
    --model data/artifacts/model_primary.pt \
    --data data/processed/full_feature_matrix.csv \
    --output data/artifacts/validation_report.json

# Sensitivity analysis over high‑packing thresholds
python code/sensitivity_analysis.py \
    --model data/artifacts/model_primary.pt \
    --data data/processed/full_feature_matrix.csv \
    --output data/artifacts/sensitivity_results.json

# Generate the final HTML report
python code/report_generator.py \
    --validation data/artifacts/validation_report.json \
    --output data/artifacts/report.html
```

## Verification Checklist
- **Dataset size**: `full_feature_matrix.csv` contains **≥ 500** rows (SC‑001).  
- **Primary model performance**: `validation_report.json` shows `spearman_rho ≥ 0.3` **and** Bonferroni‑corrected `p_value ≤ 0.05` (SC‑002).  
- **Null‑result check**: If `spearman_rho < 0.2`, the report must show `p_value ≥ 0.05` (SC‑003).  
- **Robustness**: Sensitivity table shows variation of `spearman_rho` across thresholds ≤ ±0.05 (SC‑004).  
- **Runtime**: Full pipeline completes ≤ 6 h on the GitHub Actions free tier (SC‑005).  
- **Permutation‑test deviation**: If the 4‑hour timeout fires, `validation_report.json` records `actual_shuffles` and logs the deviation (SC‑006).  

Run the test suite to confirm all unit and integration tests pass:
```bash
pytest tests/
```

## Troubleshooting
| Symptom | Possible Cause | Remedy |
|---------|----------------|--------|
| OOM during `encode_smiles.py` | Batch size too large for available RAM | Reduce `--batch-size` (default 64) or let the automatic Kaggle GPU escape hatch handle it. |
| A relatively small number of records after filtering. | Atom‑count or volume filters too strict | Inspect `data/raw/cod.jsonl` and adjust `--max-atoms` or `--volume-range` parameters. |
| Permutation test logs a timeout | CPU resources insufficient for a large number of shuffles | Accept the logged `actual_shuffles` (≥ 1 000) and note the deviation in the report (SC‑006). |
| Missing COD data | No verified COD URL supplied | Provide a verified COD mirror URL or revise the scope to an open crystallographic dataset. |

---



## projects/PROJ-511-predicting-molecular-packing-efficiency-/specs/001-predicting-molecular-packing-efficiency/contracts/dataset.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Full Feature Matrix Schema"
type: "object"
properties:
  cod_id:
    type: "string"
    description: "Unique identifier from the Crystallography Open Database."
  smiles:
    type: "string"
    description: "Canonical SMILES string representing the molecular topology."
  smiles_source:
    type: "string"
    enum:
      - "extracted"
      - "generated"
    description: "Indicates whether the SMILES was found in metadata or generated from 3D geometry."
  unit_cell_volume:
    type: "number"
    description: "Unit cell volume in cubic Angstroms."
  pc_raw:
    type: "number"
    description: "Raw Packing Coefficient (Primary Target)."
  radius_of_gyration:
    type: "number"
    description: "Radius of gyration in Angstroms."
  asphericity:
    type: "number"
    description: "Asphericity descriptor (0 to 1)."
  principal_moments:
    type: "string"
    description: "JSON string containing the three principal moments of inertia."
  lattice_system:
    type: "string"
    description: "Crystal lattice system (e.g., monoclinic, orthorhombic)."
  temperature_K:
    type:
      - "number"
      - "null"
    description: "Measurement temperature in Kelvin, or null if missing."
  has_solvent:
    type: "boolean"
    description: "True if solvent molecules are present in the crystal structure."
  atom_count:
    type: "integer"
    description: "Number of non-hydrogen atoms. (Excluded from primary regression)."
  atom_type_counts:
    type: "string"
    description: "JSON string of atom type counts (e.g., {\"C\": 10, \"O\": 2}). (Excluded from primary regression)."
  fingerprint_vector:
    type: "string"
    description: "Space-separated string of float values representing the SMILES transformer embedding."
required:
  - cod_id
  - smiles
  - smiles_source
  - unit_cell_volume
  - pc_raw
  - radius_of_gyration
  - asphericity
  - principal_moments
  - lattice_system
  - has_solvent
  - atom_count
  - atom_type_counts
  - fingerprint_vector