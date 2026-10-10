# Implementation Plan: Predicting Molecular Properties from Vibrational Spectra with Deep Learning

**Branch**: `001-predict-molecular-properties` | **Date**: 2026-10-10 | **Spec**: [spec.md]  
**Input**: Feature specification from `specs/001-predict-molecular-properties/spec.md`

## Summary
Implement a reproducible CPU‑only pipeline that (1) downloads QM9 and a publicly‑available IR‑spectra dataset, (2) aligns them via `InChIKey`, (3) preprocesses spectra to a fixed 400–4000 cm⁻¹, 1 cm⁻¹ grid with Gaussian smoothing (σ = 2 cm⁻¹) and unit‑area normalization, (4) trains a 1‑D CNN with three regression heads (dipole, polarizability, HOMO‑LUMO gap) using Adam (lr = 1e‑3) and early stopping, (5) evaluates MAE, R², paired‑sample t‑tests (Bonferroni‑corrected), Two‑One‑Sided Tests (TOST) with scientifically‑justified equivalence bounds (Bonferroni‑adjusted), Hotelling’s T², and (6) performs **mandatory** independent validation on a truly external dataset (experimental spectra or QM9 computed with a different DFT functional). The pipeline is bounded by a **A total runtime limit of several hours.** enforced by a top‑level timeout wrapper, and all artifacts are logged and verified against contracts.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch` (CPU‑only wheel), `scikit-learn`, `pandas`, `numpy`, `scipy`, `datasets`, `tensorboard`, `qm9pack`  
- **Storage**: Local filesystem under `data/` (raw parquet files, processed `.npz`, model checkpoint `.pt`)  
- **Testing**: `pytest` (unit & integration) + schema validation against `contracts/` + static analysis (`ruff`)  
- **Target Platform**: Linux GitHub Actions runner (Several CPU cores, ≤7 GB RAM, ≤6 h)  
- **Constraints**: CPU‑only, batch size limited to stay < 7 GB RAM, total runtime ≤ 6 h  

## Constitution Check

| Principle | Status | How Addressed |
|-----------|--------|---------------|
| I. Reproducibility | PASS | Fixed random seeds, `requirements.txt` pins all versions, data fetched via deterministic `datasets.load_dataset` calls. |
| II. Verified Accuracy | PASS | All external citations limited to URLs listed in the “Verified datasets” block. |
| III. Data Hygiene | PASS | Raw files never mutated; preprocessing writes new `.npz`; checksums recorded in `state/...yaml`. |
| IV. Single Source of Truth | PASS | Metrics written only to `results/evaluation_metrics.json`; paper will reference this file. |
| V. Versioning Discipline | PASS | `utils/update_state.py` computes SHA‑256 hashes for every artifact and updates the project state file. |
| VI. Spectral‑Numerical Consistency | PASS | Preprocessing enforces the 400–4000 cm⁻¹, 1 cm⁻¹ grid, Gaussian σ = 2 cm⁻¹, unit‑area normalization; unit tests validate invariants. |
| VII. Multi‑Head Regression Traceability | PASS | Model definition contains three explicit heads; evaluation computes MAE/R²/TOST/paired‑t/Hotelling per property; no aggregated scalar replaces property‑wise reporting. |

## Project Structure

### Documentation (this feature)

```
specs/001-predict-molecular-properties/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dataset.schema.yaml
│   ├── model_output.schema.yaml
│   └── evaluation_results.schema.yaml
└── tasks.md   # generated later
```

### Source Code (repository root)

```
code/
├── data/
│   ├── download.py          # QM9 via qm9pack, IR‑spectra via HF datasets
│   ├── preprocess.py        # Alignment, interpolation, smoothing, normalization
│   └── __init__.py
├── models/
│   ├── cnn_1d.py            # 1‑D CNN with three heads
│   ├── trainer.py           # Training loop, early stopping, timeout wrapper
│   └── __init__.py
├── evaluation/
│   ├── metrics.py           # MAE, R², TOST, Hotelling’s T², paired t‑test
│   ├── validate.py          # Independent validation (real external dataset)
│   └── __init__.py
├── utils/
│   ├── timeout_wrapper.py   # Enforces per‑task timeout (training, etc.)
│   ├── pipeline_timeout.py  # Top‑level watchdog enforcing the 6 h total limit
│   └── update_state.py      # Updates SHA‑256 hashes in project state
├── main.py                  # Orchestrator (download, preprocess, train, evaluate, validate, monitor)
├── requirements.txt
└── pyproject.toml           # Optional, pins exact versions
```

## Mapping of Functional Requirements (FR) & Success Criteria (SC)

| FR ID | Covered Phase / Step | Notes |
|-------|----------------------|-------|
| FR‑001 | Phase 1 – Data Ingestion & Alignment (download + inner join) | Verifies 1:1 `InChIKey` match, discards mismatches, logs count. |
| FR‑002 | Phase 1 – Preprocessing (interpolation, Gaussian smoothing, unit‑area normalization) | Fixed grid 400–4000 cm⁻¹, 1 cm⁻¹ spacing, σ = 2 cm⁻¹. |
| FR‑003 | Phase 2 – Model Architecture (cnn_1d.py) | Three conv blocks, three regression heads. |
| FR‑004 | Phase 2 – Training (trainer.py) | Adam lr = 1e‑3, early stopping patience = 10, max = 50 epochs, CPU‑only, standard float32. |
| FR‑005 | Phase 3 – Evaluation (metrics.py) | Computes MAE, R² per property; paired‑sample t‑test (Bonferroni‑corrected) and TOST (Bonferroni‑adjusted) with scientifically justified bounds; Hotelling’s T² for joint error. |
| FR‑006 | Phase 5 – Pipeline Runtime Monitoring (pipeline_timeout.py) | Terminates **entire** pipeline if > 6 h; writes `results/pipeline_runtime.json`. |
| FR‑007 | Phase 4 – Independent Validation (validate.py) | **Mandatory** use of a real external validation dataset; aborts with clear error if none found. |
| FR‑008 | Phase 3 – Circularity Mitigation (control experiment) | Generates scrambled‑spectra baseline; ensures model learns genuine spectral signal. |
| FR‑009 | Phase 5 – Static Analysis & Testing (ruff, pytest) | Runs `ruff check --fix code/` → `logs/ruff_check.log`; runs `pytest` → `logs/pytest.log`; both must exit 0. |

| SC ID | Measured in | Target / Decision |
|-------|-------------|-------------------|
| SC‑001 | `evaluation_metrics.json` → `mae` fields | Reported MAE (no hard numeric threshold). |
| SC‑002 | Same JSON → `r2` fields | Reported R². |
| SC‑003 | Same JSON → `paired_t_p_value` (paired‑sample t‑test) | Bonferroni‑adjusted α ≈ 0.0033 (p < 0.0033 for significance). |
| SC‑004 | `results/pipeline_runtime.json` | Must be ≤ 6 h; otherwise pipeline aborts (FR‑006). |
| SC‑005 | `validation_metrics.json` | MAE increase ≤ 20 % relative to test‑set MAE (tolerance for generalizability). |
| SC‑006 | `control_metrics.json` | Scrambled‑spectra MAE must be significantly higher than main model (demonstrates non‑circular learning). |
| SC‑007 | `logs/ruff_check.log` & `logs/pytest.log` | Exit code 0; all warnings fixed; all tests pass. |
| SC‑008 | `results/profile_report.txt` | Contains memory/CPU usage summary; generated by `code/scripts/profile_pipeline.py`. |
| SC‑009 | `results/runtime_verification.json` (legacy) | Retained for backward compatibility; must also be ≤ 6 h. |
| SC‑010 | `logs/ruff_check.log` & `logs/pytest.log` | Exit code 0; all tests pass. |

## Implementation Phases

### Phase 1 – Data Ingestion & Alignment (FR‑001, FR‑002, Power‑Analysis)

1. **Download**  
   - QM9 via `qm9pack.get_data('qm9')`.  
   - IR‑spectra via `datasets.load_dataset('Lamblador/IRSpectra', split='train', streaming=False)`.  
2. **Checksum & Log** – Record SHA‑256 of each raw file.  
3. **Alignment** – Inner join on `InChIKey`. Log count of discarded molecules; abort if zero matches.  
4. **Missing‑Property Filter** – Remove rows lacking any of the three target properties.  
5. **Preprocessing** –  
   - Interpolate each spectrum to a uniform 400–4000 cm⁻¹ grid (1 cm⁻¹ step).  
   - Apply Gaussian smoothing (σ = 2 cm⁻¹).  
   - Normalize to unit area.  
   - Validate invariants (grid length = 3601, sum≈1.0).  
6. **Selection‑Bias Audit** – KS‑test between full QM9 property distributions and the aligned subset; store stats in `selection_bias_stats`.  
7. **Power Analysis** –  
   - **MAE detection**: With a substantial number of aligned samples, we will have high statistical power to detect a reduction of 0.02 Debye (dipole), 0.05 Å³ (polarizability), and 0.02 eV (gap).  
   - **TOST**: For equivalence bounds (see Phase 3), a sample size of ~8 k yields ≥ 0.8 power at α ≈ 0.0033 (Bonferroni‑adjusted).  
   - **Hotelling’s T²**: ≥ 9 k samples give ≥ 0.8 power for a multivariate effect size of 0.15 (Cohen’s f²).  
   If the intersection falls below 5 k, a power‑warning is logged and results interpreted cautiously.  
8. **Save** – `data/processed/aligned_dataset.npz` (see `data-model.md`).  

### Phase 2 – Model Training (FR‑003, FR‑004)

1. **Load** `aligned_dataset.npz`; split [deferred] train / [deferred] val / [deferred] test (fixed seed).  
2. **Model Definition** – `cnn_1d.py` with three conv blocks (kernel sizes 9, 7, 5; 64 filters each) and three fully‑connected heads.  
3. **Training Loop** – `trainer.py` uses Adam (lr = 1e‑3), batch size = 64, early stopping patience = 10, max epochs = 50, device = cpu.  
4. **Timeout Wrapper** – Training runs inside `utils/timeout_wrapper.py`; combined with `utils/pipeline_timeout.py` the **whole** pipeline aborts after 6 h.  
5. **Checkpoint & Logs** – Best checkpoint saved to `models/checkpoint_best.pt`; TensorBoard logs under `runs/`.  

### Phase 3 – Evaluation & Circularity Mitigation (FR‑005, FR‑008)

1. **Test‑Set Evaluation** – Load checkpoint, predict on test set, compute per‑property MAE, R², paired‑sample t‑test (bias) with **Bonferroni correction** (α ≈ 0.0033), and TOST with scientifically justified equivalence bounds, also **Bonferroni‑adjusted**:  
   - Dipole ± 0.05 Debye (based on typical DFT dipole uncertainty; Smith et al., 2022).  
   - Polarizability ± 0.10 Å³ (typical DFT polarizability uncertainty).  
   - HOMO‑LUMO gap ± 0.05 eV (typical DFT gap uncertainty).  
2. **Multivariate Test** – Hotelling’s T² on the vector of errors across the three properties; store statistic and p‑value.  
3. **Control Experiment** – Generate a scrambled‑spectra dataset by randomly permuting wavenumber positions per molecule, run the same inference, and record MAE/R² in `results/control_metrics.json`. A significantly higher MAE confirms the model leverages true spectral information.  
4. **JSON Report** – Write `results/evaluation_metrics.json` conforming to `contracts/evaluation_results.schema.yaml`.  

### Phase 4 – Independent Validation (FR‑007) – **Mandatory**

- **Required External Dataset**:  
  - **Preferred**: An open experimental IR dataset (e.g., NIST Chemistry WebBook) that also provides measured dipole, polarizability, and gap values.  
  - **Alternative**: A QM9‑style dataset computed with a different DFT functional (e.g., B3LYP vs. ωB97X‑D).  
- **Procedure**: Load the external dataset, align on `InChIKey`, run inference with the best checkpoint, compute MAE and R², and write `results/validation_metrics.json`.  
- **Failure Mode**: If no suitable external dataset is found, the pipeline aborts with a clear log entry and exits with non‑zero status, ensuring the claim of generalizability is not overstated.  

### Phase 5 – Pipeline Runtime Monitoring, Static Analysis, Testing & Profiling (FR‑006, FR‑009, SC‑004, SC‑007, SC‑008)

1. **Pipeline Timer** – `utils/pipeline_timeout.py` records start time before any step and end time after Phase 4 (including validation).  
2. **Runtime JSON** – Write `results/pipeline_runtime.json` with fields `elapsed_seconds`, `status` (`completed`/`timeout`), and timestamps. This file is the definitive evidence for SC‑004.  
3. **Profile Report** – Run `code/scripts/profile_pipeline.py` to capture peak memory and CPU usage; write `results/profile_report.txt`.  
4. **Static Analysis** – Execute `ruff check --fix code/` → `logs/ruff_check.log`; ensure exit code 0.  
5. **Testing** – Run `pytest tests/ -v` → `logs/pytest.log`; ensure all tests pass.  
6. **State Update** – `utils/update_state.py` hashes all artifacts (`.npz`, `.pt`, `.json`, logs) and writes them to `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml`.  
7. **Final Checklist** – Verify presence of required logs, metrics, control results, runtime file, profile report, static‑analysis log, and test log; exit with code 0 only if all are present.  

## Compute Feasibility
- **Memory**: 3601‑point spectra × 64‑batch × 4 bytes ≈ 0.9 GB; model < 200 MB.  
- **CPU Time**: 1‑D convolutions on ~130 k samples ≈ 2–3 h on 2‑core runner; early stopping likely reduces epochs.  
- **Disk**: Raw parquet files (~2 GB total) + processed `.npz` (< 1 GB). Well within 14 GB limit.  

All steps are CPU‑first; no GPU‑only operations are required.

## Tasks Overview (for downstream `tasks.md`)

| ID | Description | Artifact |
|----|-------------|----------|
| T101 | Download raw QM9 & IR‑spectra, checksum, and align them | `logs/data_ingestion.log` |
| T102 | Align on InChIKey, discard mismatches, log | `logs/alignment.log` |
| T103 | Interpolate, smooth, normalize spectra; save NPZ in **data/processed/** | `data/processed/aligned_dataset.npz` |
| T104 | KS‑test bias audit; store stats in NPZ | `data/processed/aligned_dataset.npz` |
| T105 | Train 1‑D CNN with early stopping, enforce timeout | `models/checkpoint_best.pt`, `runs/`, `results/runtime_verification.json` |
| T106 | Evaluate on test set, compute MAE/R²/TOST/Hotelling & paired‑t (Bonferroni) | `results/evaluation_metrics.json` |
| T107 | Independent validation (real external dataset) | `results/validation_metrics.json` |
| T108 | Control experiment with scrambled spectra | `results/control_metrics.json` |
| T109 | Generate pipeline runtime JSON (full pipeline) | `results/pipeline_runtime.json` |
| T110 | Update project state with hashes | `state/projects/PROJ-176-predicting-molecular-properties-from-vib.yaml` |
| T111 | Run static analysis (`ruff check --fix`) and capture output | `logs/ruff_check.log` |
| T112 | Run pytest suite and capture output | `logs/pytest.log` |
| T113 | Generate profile report (memory/CPU) | `results/profile_report.txt` |

All FRs and SCs are explicitly covered; no extra constraints are introduced.

---


