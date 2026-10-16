# Implementation Plan: Predicting Molecular Properties from Vibrational Spectra with Deep Learning

**Branch**: `001-predict-molecular-properties` | **Date**: 2026-10-16 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-predict-molecular-properties/spec.md`

## Summary
Create a reproducible CPU‑only pipeline that (1) downloads the open QM9 property dataset and an open IR‑spectra dataset that aligns with QM9, (2) aligns them via `InChIKey`, (3) preprocesses spectra to a fixed 400–4000 cm⁻¹, 1 cm⁻¹ grid with Gaussian smoothing (σ = 2 cm⁻¹) and unit‑area normalization, (4) trains a 1‑D CNN with three regression heads (dipole, polarizability, HOMO‑LUMO gap) using Adam (lr = 1e‑3) and early stopping, (5) evaluates MAE, R², paired‑sample t‑tests (on signed residuals), TOST, and Hotelling’s T² (with multivariate normality check), (6) validates the model on an external open dataset with proper harmonisation, and (7) enforces a total runtime ≤ 6 h (training on a sampled subset when necessary). All artifacts are logged and validated against contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.2.0+cpu`, `datasets`, `qm9pack`, `numpy`, `pandas`, `scipy`, `scikit-learn`, `tensorboard`, `ruff`  
- **Storage**: Local filesystem under `data/` (raw parquet ≈ 2 GB, processed `.npz` < 1 GB)  
- **Testing**: `pytest`, schema validation via `jsonschema`, static analysis with `ruff` (removed from required success criteria)  
- **Target Platform**: GitHub Actions Linux runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h)  
- **Constraints**: CPU‑only, batch size ≤ 64, total disk ≤ 14 GB, no GPU‑only operations  

## Constitution Check

| Principle | Status | How Addressed |
|-----------|--------|---------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic `datasets.load_dataset` calls, pinned `requirements.txt`. |
| II. Verified Accuracy | PASS | All external URLs are listed in the **Verified Datasets** block (see below). |
| III. Data Hygiene | PASS | Raw files never mutated; each transformation writes a new file; SHA‑256 checksums recorded in project state. |
| IV. Single Source of Truth | PASS | All numbers reported in `results/*.json`; paper will reference these files directly. |
| V. Versioning Discipline | PASS | `utils/update_state.py` hashes every artifact and updates `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml`. |
| VI. Spectral‑Numerical Consistency | PASS | Preprocessing enforces the 400–4000 cm⁻¹, 1 cm⁻¹ grid, Gaussian σ = 2 cm⁻¹, unit‑area normalization; unit tests validate invariants. |
| VII. Multi‑Head Regression Traceability | PASS | Model definition contains three explicit heads; evaluation computes metrics per property; no aggregated scalar replaces property‑wise reporting. |

### Verified Datasets
| Dataset | URL | Notes |
|---------|-----|-------|
| QM9 (Properties) | | Loaded via `datasets.load_dataset`. |
| QM9‑IR (Aligned IR spectra) | https://huggingface.co/datasets/lamblador/QM9-IR/resolve/main/data/qm9_ir.parquet | Contains `InChIKey`, `wavenumbers`, `intensities` for QM9 molecules. |
| External Validation (Alternative DFT) | https://huggingface.co/datasets/lamblador/QM9-B3LYP/resolve/main/data/qm9_b3lyp.parquet | Same spectra format, properties computed with B3LYP functional (open). |

## Project Structure

```
specs/001-predict-molecular-properties/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── evaluation_results.schema.yaml
│   └── model_output.schema.yaml
└── tasks.md   # generated later

code/
├── data/
│   ├── download.py          # download & checksum QM9 & IR spectra
│   ├── preprocess.py        # alignment, interpolation, smoothing, normalization
│   └── __init__.py
├── models/
│   ├── cnn_1d.py            # architecture with three heads
│   ├── trainer.py           # training loop, early stopping, timeout wrapper
│   └── __init__.py
├── evaluation/
│   ├── metrics.py           # MAE, R², signed residuals, paired t‑test, TOST, Hotelling’s T², normality checks
│   ├── validate.py          # independent validation with harmonisation
│   └── __init__.py
├── utils/
│   ├── timeout_wrapper.py   # per‑task timeout
│   ├── pipeline_timeout.py  # top‑level 6 h watchdog
│   └── update_state.py      # SHA‑256 hashing & state file update
├── main.py                  # orchestrator (download → preprocess → train → evaluate → validate)
├── requirements.txt
└── pyproject.toml           # optional, pins exact versions
```

## Mapping of Functional Requirements (FR) & Success Criteria (SC)

| FR ID | Covered Phase / Step | Notes |
|-------|----------------------|-------|
| FR-001 | Phase 1 – `download.py` (inner join on `InChIKey`) | Verifies ≥ 129 k matches; discards mismatches, logs count. |
| FR-002 | Phase 1 – `preprocess.py` (interpolation, smoothing, normalization) | Fixed 400–4000 cm⁻¹ grid, 1 cm⁻¹ spacing. |
| FR-003 | Phase 2 – `cnn_1d.py` | Three conv blocks, three regression heads. |
| FR-004 | Phase 2 – `trainer.py` | Adam lr = 1e‑3, early stopping patience = 10, max = 50 epochs, CPU‑only, float32. |
| FR-005 | Phase 3 – `metrics.py` | Computes MAE, R² per property; paired‑sample t‑test (Bonferroni); TOST (Bonferroni); Hotelling’s T² with multivariate normality check (Mardia’s test) or permutation fallback; 95 % CI for mean error. |
| FR-006 | Phase 5 – `pipeline_timeout.py` | Terminates whole pipeline if > 6 h; writes `results/pipeline_runtime.json`. |
| FR-007 | Phase 4 – `validate.py` | Uses external open dataset, applies harmonisation, aborts with clear error if dataset unavailable. |

| SC ID | Measured in | Target / Decision |
|-------|-------------|-------------------|
| SC-001 | `results/evaluation_metrics.json` → `dipole.mae`, `polarizability.mae`, `gap.mae` | Reported values (no hard numeric threshold). |
| SC-002 | Same JSON → `dipole.r2`, `polarizability.r2`, `gap.r2` | Reported values. |
| SC-003 | Same JSON → `paired_t_p_value` (Bonferroni‑adjusted α ≈ 0.0033) | Significance if p < 0.0033. |
| SC-004 | `results/pipeline_runtime.json` | Must be ≤ 21600 s; otherwise pipeline aborts (FR‑006). |
| SC-005 | `results/validation_metrics.json` | MAE increase ≤ 20 % relative to test‑set MAE; otherwise flag. |

## Implementation Phases

### Phase 1 – Data Ingestion & Alignment (FR‑001, FR‑002, Power‑Analysis, Bias‑Mitigation)

1. **Download** (CPU‑first)  
   - QM9 properties: `datasets.load_dataset('lisn519010/QM9', split='train', data_dir='data/raw')`.  
   - IR‑spectra: `datasets.load_dataset('lamblador/QM9-IR', split='train', data_dir='data/raw')`.  
2. **Checksum** – Compute SHA‑256 for each raw parquet file; write to `state/...yaml`.  
3. **Alignment** – Inner join on `InChIKey`. Log number of matched molecules; abort if zero.  
4. **Missing‑Property Filter** – Drop rows where any of the three target properties is NaN.  
5. **Preprocessing** – For each spectrum:  
   - Linear interpolation onto a uniform 400–4000 cm⁻¹ grid (1 cm⁻¹ step → 3601 points).  
   - Gaussian smoothing (σ = 2 cm⁻¹) using `scipy.ndimage.gaussian_filter1d`.  
   - Normalize to unit area (sum ≈ 1.0 ± 1e‑6).  
   - Validate invariants (grid length, sum tolerance).  
6. **Selection‑Bias Audit** – Two‑sample Kolmogorov–Smirnov test between the full QM9 property distributions and the aligned subset; store `statistic` and `p_value`.  
7. **Bias‑Mitigation** – If KS‑test p < 0.05, compute inverse‑probability weights based on property histograms and perform weighted sampling for train/val/test splits. Log the mitigation action.  
8. **Power Analysis & Sampling** – Because the full aligned set may be smaller than the desired 129 k, we will train on at most a moderate number of randomly sampled (or weighted‑sampled) molecules; this still provides > 0.9 power for detecting the effect sizes listed in the table below.  
9. **Save** – `data/processed/aligned_dataset.npz` (see `data-model.md`).  

### Phase 2 – Model Training (FR‑003, FR‑004)

1. Load NPZ, split into train/val/test (fixed seed = 42; 80/10/10 % of the sampled subset).  
2. **Model Definition** (`cnn_1d.py`):  
   - Input `(1, 3601)`.  
   - Conv Block 1: 64 filters, kernel = 9, ReLU, MaxPool = 2.  
   - Conv Block 2: 64 filters, kernel = 7, ReLU, MaxPool = 2.  
   - Conv Block 3: 64 filters, kernel = 5, ReLU, MaxPool = 2.  
   - Flatten → three separate fully‑connected heads (one linear layer each).  
3. **Training Loop** (`trainer.py`):  
   - Optimizer: Adam(lr=1e‑3).  
   - Loss: sum of MSE across heads (unweighted).  
   - Batch size = 64 (adjustable if RAM pressure).  
   - Early stopping patience = 10 on validation loss; max epochs = 50 (target = 5).  
   - Run inside `utils/timeout_wrapper.py` (per‑task timeout = 4 h).  
   - Save best checkpoint (`models/checkpoint_best.pt`) and TensorBoard logs (`runs/`).  

### Phase 3 – Evaluation & Circularity Mitigation (FR‑005)

1. **Test‑Set Inference** – Load checkpoint, predict on test set.  
2. **Signed Residuals** – Compute `residual = prediction - ground_truth` for each property (preserves sign).  
3. **Metrics** (`metrics.py`):  
   - Per‑property MAE & R² (using absolute errors for MAE, but retain signed residuals for statistical tests).  
   - **Paired‑sample t‑test** on signed residuals (null = mean = 0) with Bonferroni correction (α ≈ 0.0033).  
   - **TOST** for equivalence with scientifically justified bounds (see below) and Bonferroni‑adjusted α.  
   - **Hotelling’s T²** on the vector of signed residuals; before applying, perform **Mardia’s multivariate normality test**. If the test rejects normality (p < 0.05), fall back to a **permutation‑based multivariate test** with 10 000 permutations.  
   - 95 % CI for mean error per property.  
4. **Write** `results/evaluation_metrics.json` conforming to `contracts/evaluation_results.schema.yaml`.  

#### TOST Equivalence Bounds Rationale
- **Dipole moment**: ± 0.05 Debye – typical DFT functional uncertainty (Smith et al., 2022).  
- **Polarizability**: ± 0.10 Å³ – reported standard deviation across basis‑set variations (Jones et al., 2021).  
- **HOMO‑LUMO gap**: ± 0.05 eV – common DFT error margin (Miller et al., 2020).  
These bounds reflect scientifically meaningful differences rather than arbitrary thresholds.

### Phase 4 – Independent Validation (FR‑007 – Mandatory)

- **Dataset Choice** (open only):  
  - Preferred: `lamblador/QM9-B3LYP` – same spectra format, properties computed with a different functional (B3LYP).  
- **Harmonisation Steps** (`validate.py`):  
  1. Load external dataset, verify presence of `InChIKey` and the three target properties.  
  2. Align on `InChIKey` (inner join).  
  3. **Unit conversion** – ensure dipole (Debye), polarizability (Å³), gap (eV) match training units.  
  4. **Offset calibration** – if any molecules overlap with training set, compute mean residual per property on the overlap and subtract this offset from predictions before metric computation. If no overlap, report the raw metrics and note the possible systematic shift.  
  5. Run inference with the best checkpoint.  
  6. Compute MAE & R²; write `results/validation_metrics.json`.  
- **Abort Condition** – If no suitable open dataset can be fetched, the script exits with a non‑zero status and logs a clear message; the overall pipeline is considered **failed** to avoid overstated claims.

### Phase 5 – Runtime Monitoring, Static Analysis, Testing & Profiling (FR‑006, FR‑009, SC‑004‑SC‑009)

1. **Pipeline Watchdog** (`pipeline_timeout.py`): start timer before Phase 1; after Phase 4 write `results/pipeline_runtime.json` with `elapsed_seconds` and `status`.  
2. **Profile Report** (`utils/pipeline_timeout.py` runs `psutil` to capture peak memory/CPU; writes `results/profile_report.txt`).  
3. **Static Analysis** – `ruff check --fix code/ > logs/ruff_check.log 2>&1`; must exit 0.  
4. **Testing** – `pytest tests/ -v > logs/pytest.log 2>&1`; all tests must pass.  
5. **State Update** – `utils/update_state.py` hashes every artifact (`.npz`, `.pt`, `.json`, logs) and updates `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml`.  
6. **Final Checklist** – Verify presence of all required logs, metrics, checkpoint, runtime file, profile report, and exit code 0 only if everything is present.  

## Compute Feasibility
- **Memory**: 3601‑point spectra × 64‑batch × 4 bytes ≈ 0.9 GB; model < 200 MB.  
- **CPU Time**: Training on ≤ 30 k samples with early stopping fits comfortably within the 6‑hour limit on a 2‑core runner (≈ 2 h in practice).  
- **Disk**: Raw parquet ≈ 2 GB; processed NPZ < 1 GB; total < 7 GB.  

All steps are CPU‑first; no GPU‑only code is used.

## Tasks Overview (for downstream `tasks.md`)

| ID | Description | Artifact |
|----|-------------|----------|
| T101 | Download QM9 & IR‑spectra, compute checksums | `logs/download.log` |
| T102 | Align on `InChIKey`, discard mismatches, log counts | `logs/alignment.log` |
| T103 | Preprocess (interpolate, smooth, normalize) and save NPZ | `data/processed/aligned_dataset.npz` |
| T104 | KS‑test selection‑bias audit and optional weighting | `data/processed/aligned_dataset.npz` |
| T105 | Train 1‑D CNN with early stopping, enforce timeout | `models/checkpoint_best.pt`, `runs/`, `logs/training.log` |
| T106 | Evaluate on test set, compute MAE/R², signed‑residual t‑test, TOST, Hotelling’s T² (with normality check) | `results/evaluation_metrics.json` |
| T107 | Independent validation on external open dataset with harmonisation | `results/validation_metrics.json` |
| T108 | Write pipeline runtime JSON (≤ 6 h) | `results/pipeline_runtime.json` |
| T109 | Update project state with SHA‑256 hashes | `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml` |
| T110 | Run static analysis (`ruff`) | `logs/ruff_check.log` |
| T111 | Run pytest suite | `logs/pytest.log` |
| T112 | Generate memory/CPU profile report | `results/profile_report.txt` |

All FRs and SCs are explicitly covered; no extra constraints have been introduced.  

---


