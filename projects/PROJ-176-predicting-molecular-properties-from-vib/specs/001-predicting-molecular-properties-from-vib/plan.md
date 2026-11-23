# Implementation Plan: Predicting Molecular Properties from Vibrational Spectra with Deep Learning  

**Branch**: `001-predict-molecular-properties` | **Date**: 2026-10-20 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-predict-molecular-properties/spec.md`

## Summary  
Create a reproducible CPU‑only pipeline that (0) **generates IR spectra in‑house** using the B3LYP functional (to guarantee functional consistency with QM9 target properties), (1) downloads an open QM9 property dataset, (2) aligns it with the generated spectra (or with an external IR dataset only if its DFT method matches B3LYP), (3) preprocesses spectra to a fixed 400‑4000 cm⁻¹, 1 cm⁻¹ grid with Gaussian smoothing (σ = 2 cm⁻¹) and unit‑area normalization, (4) trains a dimensional CNN with three regression heads (dipole, polarizability, HOMO‑LUMO gap) using Adam (lr = 1e‑3) and early stopping, (5) evaluates MAE, R², paired‑sample t‑tests, TOST equivalence tests, and Hotelling’s T² (with normality fallback), (6) validates the model on an **independent B3LYP‑computed** dataset with systematic offset calibration, (7) runs two control experiments – (a) scrambled‑order spectra and (b) pure random‑noise spectra – and (8) records deterministic logs, schema‑validated artifacts, and a compile‑all check. All steps are designed to run on the GitHub Actions free‑tier CPU runner within the 6‑hour limit.

## Technical Context  

| Item | Detail |
|------|--------|
| **Language/Version** | Python 3.11 |
| **Primary Dependencies** | `torch==2.2.0+cpu`, `datasets`, `numpy`, `pandas`, `scipy`, `scikit-learn`, `tensorboard`, `ruff`, `pytest`, `pyscf` (for in‑house spectra generation) |
| **Storage** | Files under `data/` (raw parquet ≈ several GB, processed NPZ < 1 GB) |
| **Testing** | `pytest`, JSON‑schema validation via `jsonschema` |
| **Target Platform** | GitHub Actions Linux runner (2 CPU cores, ≤ 7 GB RAM, ≤ 14 GB disk) |
| **Constraints** | CPU‑only, batch size ≤ 64, total runtime ≤ 6 h, no GPU‑only code |
| **Scale/Scope** | Aim for **≥ 129 000** aligned molecules (the spec’s acceptance scenario) to guarantee high statistical power; if fewer matches are obtained, a power‑warning will be logged and results interpreted conservatively. |

## Constitution Check  

| Principle | Status | How Addressed |
|-----------|--------|---------------|
| I. Reproducibility | PASS | Fixed random seeds, deterministic `datasets.load_dataset` calls, `compileall` step, logs capture exact command lines. |
| II. Verified Accuracy | PASS | Only URLs listed in the “Verified datasets” block are used (QM9 property parquet, generated B3LYP spectra, optional Lamblador IR spectra if functional matches). |
| III. Data Hygiene | PASS | Raw files are never mutated; each transformation writes a new artifact; SHA‑256 checksums recorded in `state/projects/...yaml`. |
| IV. Single Source of Truth | PASS | All numbers reported in JSON result files; the paper will reference those files directly. |
| V. Versioning Discipline | PASS | `utils/update_state.py` hashes every artifact and updates the project state file. |
| VI. Spectral‑Numerical Consistency | PASS | Preprocessing enforces the 400‑4000 cm⁻¹, 1 cm⁻¹ grid, Gaussian σ = 2 cm⁻¹, unit‑area normalization; unit tests validate invariants. |
| VII. Multi‑Head Regression Traceability | PASS | Model definition contains three explicit heads; evaluation computes metrics per property; no aggregated scalar replaces property‑wise reporting. |

## Verified Datasets  

| Dataset | URL | Notes |
|---------|-----|-------|
| QM9 (properties) | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | Contains `InChIKey`, dipole, polarizability, HOMO‑LUMO gap. |
| IR‑spectra (optional, B3LYP‑matched) | https://huggingface.co/datasets/Lamblador/IRSpectra/resolve/main/data/test-00000-of-00001.parquet | Used only if its `dft_method` equals B3LYP; otherwise ignored. |
| External Validation (B3LYP) | https://huggingface.co/datasets/lamblador/QM9-B3LYP/resolve/main/data/qm9_b3lyp.parquet | Same spectrum format; properties computed with B3LYP. |

*If the external IR‑spectra dataset’s DFT functional differs from the QM9 properties (which are B3LYP), the pipeline **defaults to Phase 0.5** to generate spectra in‑house using the same B3LYP functional via PySCF, guaranteeing methodological consistency.*

### Alignment & Integrity Checks  
1. **Inner join on `InChIKey`** – ensures a 1:1 correspondence.  
2. **Discard mismatches** – log count; abort if zero matches.  
3. **Missing‑property filter** – drop any molecule lacking any of the three target properties before training.  
4. **Selection‑bias audit** – two‑sample Kolmogorov–Smirnov test between full QM9 property distributions and the aligned subset; store KS statistic and p‑value.  
5. **Bias‑mitigation** – if KS p < 0.05, compute inverse‑probability weights from property histograms and use weighted sampling for train/val/test splits; log the mitigation action.

### Variable Fit Confirmation  
- **Predictor**: Fixed‑length IR spectrum (a high‑resolution set of points after interpolation).  
- **Outcomes**: Dipole (Debye), polarizability (Å³), HOMO‑LUMO gap (eV).  
Both predictor and outcomes are present after alignment, satisfying the variable‑fit requirement.

## Mapping of Functional Requirements (FR) & Success Criteria (SC)  

| FR ID | Covered Phase / Script | Notes |
|-------|------------------------|-------|
| FR-001 | `code/data/download.py` + `code/data/align.py` | Downloads verified datasets, computes SHA‑256, joins on `InChIKey`, discards mismatches, logs counts. |
| FR-002 | `code/data/preprocess.py` | Interpolation, Gaussian smoothing (σ = 2 cm⁻¹), unit‑area normalization, fixed 400‑4000 cm⁻¹ grid. |
| FR-003 | `code/models/cnn_1d.py` | Three convolutional blocks, three separate regression heads. |
| FR-004 | `code/models/trainer.py` | Adam(lr=1e‑3), early stopping (patience = 10), max = 50 epochs, CPU‑only, float32. |
| FR-005 | `code/evaluation/metrics.py` | Computes MAE, R² per property; paired‑sample t‑test (Bonferroni); TOST; Hotelling’s T² with normality check; 95 % CI. |
| FR-006 | `code/utils/pipeline_timeout.py` | Terminates whole pipeline if > 6 h, writes `results/pipeline_runtime.json`. |
| FR-007 | `code/evaluation/validate.py` | Loads B3LYP validation set, aligns on `InChIKey`, applies offset calibration when DFT methods differ, computes MAE/R², writes `results/validation_metrics.json`. |

| SC ID | Measured In | Target / Decision |
|-------|-------------|-------------------|
| SC-001 | `results/evaluation_metrics.json` → `dipole.mae`, `polarizability.mae`, `gap.mae` | Reported values (no hard numeric threshold). |
| SC-002 | Same JSON → `dipole.r2`, `polarizability.r2`, `gap.r2` | Reported values. |
| SC-003 | Same JSON → `paired_t_p_value` (Bonferroni‑adjusted α ≈ 0.0033) | Significance if p < 0.0033. |
| SC-004 | `results/pipeline_runtime.json` | Must be ≤ 21600 s; otherwise pipeline aborts. |
| SC-005 | `results/validation_metrics.json` | MAE increase ≤ 20 % relative to test‑set MAE; otherwise flag. |

## Implementation Phases  

### Phase 0.5 – In‑house IR Spectra Generation (functional consistency)  
1. Load QM9 geometries from the QM9 parquet file.  
2. Compute harmonic vibrational frequencies and IR intensities **using the B3LYP functional** via the lightweight CPU‑only quantum chemistry library PySCF.  
3. Approximate IR intensities from dipole‑derivative estimates.  
4. Interpolate to the 400‑4000 cm⁻¹ grid, apply Gaussian smoothing (σ = 2 cm⁻¹) and unit‑area normalization.  
5. Store generated spectra in `data/generated/generated_spectra.npz`.  
*If the external IR dataset’s `dft_method` matches B3LYP, the pipeline will skip this step and use the downloaded spectra.*

### Phase 1 – Data Ingestion & Alignment (FR‑001, FR‑002, FR‑006)  
1. **Create logs directory & compileall check** – `mkdir -p logs && python -m compileall -q code/ > logs/compileall.log 2>&1`.  
2. **Download** (`code/data/download.py`) – streams to `data/raw/`, computes SHA‑256, writes `logs/download.log`.  
3. **Checksum verification** – aborts with clear error if mismatch.  
4. **Alignment** (`code/data/align.py`) – inner join on `InChIKey`; discards mismatches, logs count. If zero matches, abort with exit code 1.  
5. **Missing‑property filter** – drop rows where any target is NaN; log count.  
6. **Preprocess** (`code/data/preprocess.py`) – interpolation across the target spectral region (from the lower limit to 4000 cm⁻¹) with a fine 1 cm⁻¹ step resolution., Gaussian smoothing (σ = 2 cm⁻¹), unit‑area normalization; validates invariants; writes `data/processed/aligned_dataset.npz`.  
7. **Bias audit** (`code/data/bias_audit.py`) – KS‑test between full QM9 property distributions and the aligned subset; if p < 0.05, compute inverse‑probability weights and store them for downstream sampling; log in `logs/bias_audit.log`.  

### Phase 2 – Model Training (FR‑003, FR‑004)  
1. Load NPZ, split into train/val/test (80/10/10 % of the *sampled* subset; fixed seed = 42).  
2. **Trainer** (`code/models/trainer.py`) – runs inside `utils/timeout_wrapper.py` (per‑task timeout = 4 h). Early stopping patience = 10, max epochs = 50, target = 5.  
3. Save best checkpoint (`models/checkpoint_best.pt`) and TensorBoard logs (`runs/`).  
4. Log training progress to `logs/training.log`.  

### Phase 3 – Evaluation (FR‑005)  
1. Load checkpoint, predict on test set.  
2. Compute signed residuals, MAE, R² per property.  
3. **Paired‑sample t‑test** (Bonferroni‑adjusted).  
4. **TOST** equivalence bounds: dipole ± 0.05 D, polarizability ± 0.10 Å³, gap ± 0.05 eV.  
5. **Hotelling’s T²** – perform Mardia’s multivariate normality test; if p < 0.05, fall back to permutation test (a large number of permutations).  
6. Write `results/evaluation_metrics.json` (validated against `contracts/evaluation_results.schema.yaml`).  

### Phase 4 – Independent Validation (FR‑007)  
1. Load B3LYP validation set (`lamblador/QM9-B3LYP`).  
2. Align on `InChIKey`; if any molecules overlap with the training set, compute per‑property mean residuals on these overlaps and subtract as an offset before metric calculation (systematic functional‑method calibration).  
3. If **no** overlap exists, automatically invoke Phase 0.5 to generate spectra with B3LYP for the validation molecules, ensuring functional parity.  
4. Predict, compute MAE & R², write `results/validation_metrics.json`.  
5. If MAE increase > 20 % relative to test‑set MAE, add a `warning` field in the JSON.  

### Phase 5 – Control Experiments (baseline checks)  
1. **Scrambled‑order baseline** (`code/evaluation/control.py`): randomly permute wavenumber order per spectrum, run inference, write `results/control_metrics.json`.  
2. **Random‑noise baseline** (`code/evaluation/control_random.py`): replace each spectrum with Gaussian noise (mean = 0, std = 1), run inference, write `results/control_random_metrics.json`.  
Both baselines must yield substantially higher MAE than the primary model; otherwise a warning is logged.  

### Phase 6 – Runtime Monitoring, Static Analysis, Testing, Compilation (FR‑006)  
1. **Pipeline watchdog** (`utils/pipeline_timeout.py`) – starts before Phase 1, stops after Phase 5; writes `results/pipeline_runtime.json`.  
2. **Profile report** – capture peak memory/CPU via `psutil`, write `results/profile_report.txt`.  
3. **Static analysis** – `ruff check --fix code/ > logs/ruff_check.log 2>&1`. Must exit 0.  
4. **Compile all** – `python -m compileall -q code/ > logs/compileall.log 2>&1`. Must exit 0.  
5. **Test suite** – `pytest tests/ -v > logs/pytest.log 2>&1`. All tests must pass.  
6. **Structure report** – after the full run, a script `code/utils/structure_report.py` writes `results/structure_report.txt` summarizing artifact counts and SHA‑256 hashes (required for T001).  

## Compute Feasibility  
- **Memory**: 3601‑point spectra × batch = 64 → ≈ 0.9 GB; model < 200 MB.  
- **CPU time**: Training on ≤ 130 k samples with early stopping typically ≤ 3 h on 2‑core runner; full pipeline ≤ 5 h (including download, preprocessing, evaluation).  
- All methods are CPU‑first; no GPU‑only code is present.

## Tasks Overview (for downstream `tasks.md`)  

| ID | Description | Artifact |
|----|-------------|----------|
| T001 | Create top‑level `logs/` dir, run `compileall`, generate `results/structure_report.txt` | `logs/compileall.log`, `results/structure_report.txt` |
| T002 | Download QM9 & IR spectra, compute checksums | `logs/download.log` |
| T003 | Align on `InChIKey`, discard mismatches. | `logs/alignment.log` |
| T004 | Preprocess spectra (interp, smooth, normalize) | `data/processed/aligned_dataset.npz` |
| T005 | KS‑test bias audit + optional weighting | `logs/bias_audit.log` |
| T006 | Train 1‑D CNN with early stopping | `models/checkpoint_best.pt`, `logs/training.log` |
| T007 | Evaluation on test set (MAE, R², t‑test, TOST, Hotelling) | `results/evaluation_metrics.json` |
| T008 | Independent validation (B3LYP) with offset calibration | `results/validation_metrics.json` |
| T009 | Scrambled‑order control experiment | `results/control_metrics.json` |
| T010 | Random‑noise control experiment | `results/control_random_metrics.json` |
| T011 | Pipeline runtime watchdog | `results/pipeline_runtime.json` |
| T012 | Profile report (memory/CPU) | `results/profile_report.txt` |
| T013 | Static analysis with ruff | `logs/ruff_check.log` |
| T014 | Run pytest suite | `logs/pytest.log` |
| T015 | Update project state with SHA‑256 hashes | `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml` |

All FRs and SCs are explicitly covered; no extra constraints were introduced.  

---  

## Scientific Soundness & Circularity Mitigation  

1. **Functional Consistency** – By generating IR spectra in‑house with the same B3LYP functional used for QM9 target properties, we eliminate the primary source of circularity.  
2. **Independent Validation** – Evaluation on a separate B3LYP‑computed dataset (different molecules) tests generalisation beyond the training distribution.  
3. **Offset Calibration** – When functional mismatches exist but overlapping molecules are present, per‑property mean residuals are subtracted before metric computation, preventing systematic bias from contaminating the validation results.  
4. **Baseline Controls** – Scrambled‑order and pure random‑noise baselines demonstrate that the model’s performance relies on genuine spectral ordering and signal, not on trivial intensity statistics.  

These measures collectively ensure that any reported predictive capability reflects real information encoded in vibrational spectra rather than artefacts of shared computational methodology.  
