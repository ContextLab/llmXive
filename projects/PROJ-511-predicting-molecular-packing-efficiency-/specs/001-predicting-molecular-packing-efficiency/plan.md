# Implementation Plan: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Branch**: `PROJ-511-packing-efficiency` | **Date**: 2026-06-29 | **Spec**: [spec.md](../specs/PROJ-511-packing-efficiency/spec.md)  
**Input**: Feature specification from `/specs/PROJ-511-packing-efficiency/spec.md`

## Summary
The project must (1) download the Crystallography Open Database (COD), filter organic crystals with < 50 atoms, compute packing coefficients, and derive canonical SMILES strings; (2) encode SMILES with a frozen, CPU‑compatible SMILES‑Transformer to obtain fixed‑length fingerprint vectors; (3) train a lightweight 2‑layer MLP (≤ 100 k parameters, architecture identifier `MLP-128-1`) on the fingerprint‑target pairs; (4) evaluate the model on a held‑out validation split, reporting MAE, Pearson r, and Spearman ρ; (5) assess statistical significance via a 1 000‑iteration permutation test and a sensitivity sweep over p‑value thresholds {0.01, 0.05, 0.10}; (6) log all steps, diagnostics, and final metrics to `report.txt`; and (7) validate all intermediate artifacts against the JSON‑schema contracts. All steps must be reproducible on a free‑tier GitHub Actions runner (2 CPU cores, ~7 GB RAM, ≤ 6 h runtime).

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**:
- `rdkit>=2023.09.3` (CIF parsing & SMILES generation)  
- `torch==2.2.0+cpu` (MLP training, frozen transformer inference)  
- `transformers==4.41.2` (SMILES‑Transformer model)  
- `pandas==2.2.2` (CSV handling)  
- `numpy==1.26.4`  
- `scikit-learn==1.5.0` (train/val split, metrics)  
- `scipy==1.13.1` (Shapiro‑Wilk, permutation test)  
- `matplotlib==3.9.0` (diagnostic plots)  
- `tqdm==4.66.5` (progress bars)  
- `huggingface_hub==0.23.0` (model download)

**Storage**: CSV files under `data/`, intermediate NumPy arrays, model checkpoint (`model.pt`), figures (`figures/`).  
**Testing**: `pytest` with contract‑based validation of CSV schema (`contracts/dataset.schema.yaml`) and model artifact (`contracts/model.schema.yaml`).  
**Target Platform**: Linux (Ubuntu‑22.04) GitHub Actions runner.  
**Performance Goals**: End‑to‑end runtime ≤ 6 h, peak RAM ≤ 2 GB.  
**Constraints**: CPU‑only, no GPU, no large‑memory models; all libraries must install on the free‑tier runner.  
**Scale/Scope**: Target curated dataset of **≥ 950** paired samples (max 1000) to achieve ≥ 0.80 statistical power for an expected effect size r≈0.4. If fewer organic entries are available, the pipeline will use all retained entries (minimum 500) and log the reduced power in `report.txt`.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| I. Reproducibility | All random seeds are fixed (`numpy.random.seed(42)`, `torch.manual_seed(42)`). Data download uses the official COD script; the same URL is used on every run. |
| II. Verified Accuracy | No external citations are introduced in the plan; any later paper will be vetted by the Reference‑Validator. |
| III. Data Hygiene | Raw COD CIF files are stored unchanged under `data/raw/`. Every transformation produces a new file with a provenance tag (`<COD_ID>_processed.csv`). Checksums are recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | **`data/processed/dataset.csv` is designated the single source of truth** for all downstream analyses; every figure and statistic is generated directly from this file. |
| V. Versioning Discipline | All artifacts (CSV, model checkpoint, report) are version‑hashed and recorded in the project state file. |
| VI. Open Crystallographic Data Integrity | COD entries are fetched directly from the official COD download archive. Each `DatasetEntry` stores the COD identifier for traceability. |
| VII. Model Transparency and Statistical Validation | The frozen SMILES‑Transformer and the 2‑layer MLP (`MLP-128-1`) are fully specified in `code/`. Permutation test and sensitivity analysis are executed and logged. |

All principles are satisfied; no violations detected.

## Project Structure
```text
src/
├── data/
│   ├── raw/                     # Raw COD CIF files (unchanged)
│   ├── processed/               # Processed CSVs, fingerprints, etc.
│   └── figures/                 # Diagnostic plots & final figures
├── models/
│   └── mlp.py                   # 2‑layer MLP definition (`MLP-128-1`) & training loop
├── pipelines/
│   ├── download_cod.py          # COD download & extraction
│   ├── prepare_dataset.py       # CIF parsing, SMILES generation, packing coeff.
│   ├── fingerprint.py           # Load SMILES‑Transformer & generate fingerprints
│   ├── train.py                 # Train MLP, save `model.pt`
│   ├── evaluate.py              # Validation metrics, plots
│   └── significance.py          # Permutation test & sensitivity sweep
├── utils/
│   ├── chemistry.py             # vdW radii table, volume calculations
│   └── logging.py               # Standardized `report.txt` writer
└── main.py                      # Orchestrates the full pipeline
```
**Structure Decision**: A single‑repo layout with clear separation between data, models, pipelines, and utilities. This satisfies reproducibility and versioning requirements while keeping the CI footprint small.

## Complexity Tracking
No constitution‑driven complexity violations identified. All required functionality can be implemented within the chosen structure and compute budget.

## Methodological Limitations
- **SMILES‑only representation**: SMILES captures 2‑D connectivity but not 3‑D conformations, intermolecular contacts, or solvent effects that influence crystal packing. Consequently, the study is **exploratory** and limited to associative findings; causal claims are avoided.
- **Packing coefficient proxy**: The packing coefficient (unit‑cell volume ÷ Σ vdW volumes) ignores crystal‑specific factors such as voids, disorder, and solvent inclusion. Results are interpreted with this construct‑validity caveat.
- **Dataset size & power**: Power analysis (α = 0.05, two‑tailed) indicates that **N ≥ 950** yields ≈ 0.90 power for an expected r ≈ 0.4 (≥ 0.80 threshold satisfied). If the COD provides fewer organic entries, the pipeline will still run (minimum 500) but will log the reduced power in `report.txt`.

## Statistical Rigor Checklist
- **Multiple‑comparison correction**: Not required (single primary correlation test).  
- **Power justification**: Target N ≥ 950 → power ≈ 0.90 for an expected r ≈ 0.4 (≥ 0.80 target). If N < 950, reduced power is reported.  
- **Causal inference**: Observational study; claims limited to association.  
- **Measurement validity**: Packing coefficient derived from standard crystallographic calculations; vdW radii from Bondi (1964). SMILES‑Transformer pretrained on a large corpus of SMILES (publicly documented).  
- **Collinearity**: Fingerprint dimensions are highly correlated by design; the MLP treats the vector as a whole, and no independent‑predictor claims are made.

## Success Criteria (explicit mapping to SCs)
- **SC‑001**: Pearson r ≥ 0.4 (predictive) **or** r < 0.2 (null finding) on the validation set.  
- **SC‑002**: MAE ≤ 0.05 on the validation set.  
- **SC‑003**: Permutation‑test p‑value < 0.05.  
- **SC‑004**: Significance decision unchanged for α = 0.01, 0.05, 0.10.  
- **SC‑005**: End‑to‑end pipeline completes on free‑tier CI within 6 h and ≤ 2 GB RAM.  
- **SC‑006**: Diagnostic thresholds – Shapiro‑Wilk p > 0.05, no heteroscedasticity (Breusch‑Pagan p > 0.05), Spearman ρ ≥ 0.4; all recorded in `report.txt`.

## Pipeline Overview & Ordered Tasks

1. **Data Acquisition (FR‑001)** – `pipelines/download_cod.py`  
   - Download latest COD release via official script.  
   - Verify SHA‑256 checksum; record in `state/projects/...yaml`.

2. **Filtering (FR‑001)** – `pipelines/prepare_dataset.py`  
   - Retain entries with < 50 non‑hydrogen atoms **and** organic composition (C, H, N, O, S, P, halogens only).  
   - Log retained count.

3. **Parsing & Packing Coefficient (FR‑002)** – same script  
   - Compute unit‑cell volume from CIF parameters.  
   - Sum atomic vdW volumes (Bondi radii).  
   - Calculate packing coefficient; skip entries lacking required fields (edge‑case handling).

4. **SMILES Generation (FR‑003)** – same script  
   - Build RDKit `Mol` from CIF atom coordinates, generate canonical SMILES.  
   - Log and skip failures.

5. **Fingerprint Extraction (FR‑004)** – `pipelines/fingerprint.py`  
   - Load frozen SMILES‑Transformer (`seyonec/PubChem10M_SMILES_BPE_60k`) on CPU.  
   - Tokenize SMILES, pass through transformer, mean‑pool hidden states → 768‑dim vector.  

6. **Dataset Assembly & SSoT Declaration (FR‑010)** – `pipelines/prepare_dataset.py`  
   - Write `data/processed/dataset.csv` with required columns (see data‑model).  
   - Split into training and validation using `train_test_split(..., test_size=0.2, random_state=42)`.  
   - **Contract Validation**: `pytest -q` validates `dataset.csv` against `contracts/dataset.schema.yaml`.  

7. **Model Training (FR‑005)** – `pipelines/train.py`  
   - Define **2‑layer MLP `MLP-128-1`**: Input 768 → Hidden 128 (ReLU) → Output 1 (linear).  
   - ≤ 100 k parameters (≈ 98 k).  
   - Train ≤ 5 epochs, Adam lr 1e‑3, batch 32, early stopping.  
   - Save `models/model.pt`.  
   - **Contract Validation**: `pytest -q` validates `model.pt` against `contracts/model.schema.yaml`.  

8. **Model Evaluation (FR‑006, FR‑011)** – `pipelines/evaluate.py`  
   - Predict on validation set.  
   - Compute **MAE**, **Pearson r**, **Spearman ρ**.  
   - Generate scatter plot and residual diagnostics:  
     - Shapiro‑Wilk test on residuals (require p > 0.05).  
     - Breusch‑Pagan test for heteroscedasticity (require p > 0.05).  
   - Record all metrics, diagnostic p‑values, and **Spearman ρ ≥ 0.4** in `report.txt`.  

9. **Statistical Significance & Robustness (FR‑007, FR‑008)** – `pipelines/significance.py`  
   - **Permutation test**: 1 000 shuffles → empirical p‑value (< 0.05 required).  
   - **Sensitivity sweep**: repeat at α = 0.01 and α = 0.10; verify unchanged significance decision (SC‑004).  

10. **Logging & Reporting (FR‑009)** – `utils/logging.py`  
    - Structured `pipeline.log` + human‑readable `report.txt` (includes all SC thresholds and power note).  

All steps respect the ordered dependencies (download → processing → fingerprint → split → train → evaluate → significance → reporting) and stay within the CI compute budget.

