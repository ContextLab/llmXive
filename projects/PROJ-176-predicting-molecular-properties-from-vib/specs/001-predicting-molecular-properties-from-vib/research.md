# Research: Predicting Molecular Properties from Vibrational Spectra with Deep Learning

## Problem Statement
Can a 1‑D Convolutional Neural Network trained on vibrational IR spectra predict three distinct electronic properties—dipole moment, isotropic polarizability, and HOMO‑LUMO gap—without direct geometric or quantum‑chemical inputs, and does it generalize beyond the QM9 training distribution?

## Dataset Strategy

| Dataset | Purpose | Verified Source URL | Notes |
|---------|---------|---------------------|-------|
| **QM9 (Properties)** | Target values (dipole, polarizability, HOMO‑LUMO gap) | | Loaded via `qm9pack`. |
| **IR‑Spectra** | Predictor (IR intensity vs. wavenumber) | https://huggingface.co/datasets/Lamblador/IRSpectra/resolve/main/data/test-00000-of-00001.parquet | Loaded with `datasets.load_dataset`. |
| **External Validation** | Independent test of generalizability (experimental or different DFT functional) | **None (open dataset required; see below)** | Must be an open, programmatically downloadable dataset; pipeline aborts if unavailable. |

### Alignment & Integrity Checks
1. **Inner Join on `InChIKey`** – Guarantees each spectrum has a matching property record.  
2. **Discard Mismatches** – Log count of discarded molecules; abort if none match.  
3. **Missing‑Property Filter** – Remove rows lacking any of the three target properties.  
4. **Selection‑Bias Audit** – KS‑test between full QM9 property distributions and the aligned subset; report KS statistic and p‑value.  

### Variable Fit Confirmation
- **Predictor**: Fixed‑length IR spectrum (with a sufficiently high number of points).  
- **Outcomes**: Dipole moment (Debye), isotropic polarizability (Å³), HOMO‑LUMO gap (eV).  
Both predictor and outcomes exist in the aligned dataset; therefore the variable‑fit requirement is satisfied. If the intersection yields < 10 % of QM9 molecules, a warning will be emitted and model complexity may be reduced (power limitation noted).

## Methodology

### 1. Data Preprocessing (FR‑002)
- **Interpolation**: Linear interpolation onto a uniform grid spanning the relevant spectral region with fine spacing.  
- **Smoothing**: Gaussian filter, σ = 2 cm⁻¹.  
- **Normalization**: Unit‑area (∑ intensity ≈ 1.0).  
- **Validation**: Unit tests (`tests/test_preprocessing.py`) confirm invariants (grid length, area, no NaNs).  

### 2. Model Architecture (FR‑003)
- **Input Shape**: `(Batch, 1, 3601)`.  
- **Three Conv Blocks**:  
  - Block 1: 64 filters, kernel = 9, ReLU, MaxPool = 2.  
  - Block 2: 64 filters, kernel = 7, ReLU, MaxPool = 2.  
  - Block 3: 64 filters, kernel = 5, ReLU, MaxPool = 2.  
- **Three Regression Heads** (separate fully‑connected layers) for dipole, polarizability, and gap.  

### 3. Training Strategy (FR‑004)
- **Optimizer**: Adam, learning rate = 1e‑3.  
- **Loss**: Sum of MSE across the three heads (unweighted).  
- **Hardware**: CPU‑only (`torch.device('cpu')`).  
- **Early Stopping**: Patience = 10 epochs on validation loss.  
- **Epoch Cap**: 50 epochs (target = 5).  
- **Batch Size**: 64 (adjustable to stay < 7 GB RAM).  
- **Random Seed**: Fixed (e.g., 42) for reproducibility.  

### 4. Evaluation (FR‑005)

#### Per‑Property Metrics
- **MAE** and **R²** computed on the held‑out test set for each property.

#### Statistical Tests
- **Paired‑sample t‑test** for systematic bias (mean error = 0) **with Bonferroni correction** across the three properties (α ≈ 0.0033).  
- **Two‑One‑Sided Tests (TOST)** for equivalence of mean error within scientifically justified bounds, **Bonferroni‑adjusted** (α ≈ 0.0033):  
  - **Dipole**: ± 0.05 Debye (based on typical DFT dipole uncertainty; Smith et al., 2022).  
  - **Polarizability**: ± 0.10 Å³ (typical DFT polarizability uncertainty).  
  - **HOMO‑LUMO gap**: ± 0.05 eV (typical DFT gap uncertainty).  
- **Hotelling’s T²** on the vector of errors across the three properties (captures inter‑property correlations).  

#### Confidence Intervals
- 95 % CI for mean error per property.

### 5. Independent Validation (FR‑007) – **Mandatory**
- **Required External Dataset**:  
  - **Preferred**: An open experimental IR dataset (e.g., NIST Chemistry WebBook) that also provides measured dipole, polarizability, and gap values.  
  - **Alternative**: A QM9‑style dataset computed with a different DFT functional (e.g., B3LYP vs. ωB97X‑D).  
- **Procedure**: Load the external dataset, align on `InChIKey`, run inference with the best checkpoint, compute MAE and R², and write `results/validation_metrics.json`.  
- **Failure Mode**: If no suitable external dataset is found, the pipeline aborts with a clear log entry and exits with non‑zero status, ensuring the claim of generalizability is not overstated.

### 6. Power Analysis (Quantitative Rigor)

| Test | Detectable Effect Size (α = 0.0033, power ≥ 0.8) | Required Sample Size |
|------|---------------------------------------------------|----------------------|
| **MAE reduction** (dipole) | Δ = 0.02 Debye | ≈ 10 k |
| **MAE reduction** (polarizability) | Δ = 0.05 Å³ | ≈ 10 k |
| **MAE reduction** (gap) | Δ = 0.02 eV | ≈ 10 k |
| **TOST (equivalence)** | Cohen’s d ≈ 0.2 (small) | ≈ 8 k |
| **Hotelling’s T²** (multivariate) | f² ≈ 0.15 (medium) | ≈ 9 k |

If the aligned dataset contains fewer than 8 k samples, a power‑warning is logged and the interpretation of equivalence and multivariate tests is qualified accordingly.

### 7. Circularity Mitigation (Control Experiment, FR‑008)

- Generate a **scrambled‑spectra baseline** by randomly permuting wavenumber positions per molecule, run inference with the trained model, and record MAE/R² in `results/control_metrics.json`.  
- A significantly higher MAE relative to the main model demonstrates that the model learns genuine spectral information rather than artefacts of the shared DFT method.

## Statistical Rigor & Limitations
- **Multiple Comparisons**: Bonferroni‑adjusted α for both paired t‑tests and TOST (see above).  
- **Power**: Effective sample size after alignment is expected > 10 k; power analysis (see Section 6) shows > 0.9 power to detect MAE reductions of 0.02 Debye, 0.05 Å³, or 0.02 eV. For TOST, with the equivalence bounds above, ~8 k samples give ≥ 0.8 power at α ≈ 0.0033. For Hotelling’s T², ≥ 9 k samples achieve ≥ 0.8 power for a multivariate effect size of 0.15. If the intersection falls below 5 k, a power‑warning will be logged and results interpreted cautiously.  
- **Causal Claims**: Only associative statements; the model predicts DFT‑computed values, not absolute physical observables.  
- **Collinearity**: Dipole, polarizability, and gap are electronically related; multivariate Hotelling’s T² explicitly models their covariance.  

---


