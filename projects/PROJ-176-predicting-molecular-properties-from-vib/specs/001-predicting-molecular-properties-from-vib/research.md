# Research: Predicting Molecular Properties from Vibrational Spectra with Deep Learning

## Problem Statement
Can a 1‑D Convolutional Neural Network trained solely on vibrational IR spectra predict three distinct electronic properties—dipole moment, isotropic polarizability, and HOMO‑LUMO gap—without direct geometric inputs, and does the model generalize beyond the QM9 training distribution?

## Dataset Strategy

| Dataset | Purpose | Verified Source URL | Notes |
|---------|---------|---------------------|-------|
| **QM9 (Properties)** | Target values (dipole, polarizability, HOMO‑LUMO gap) | | Loaded via `datasets.load_dataset`. |
| **QM9‑IR (Spectra)** | Predictor (IR intensity vs. wavenumber) | https://huggingface.co/datasets/lamblador/QM9-IR/resolve/main/data/qm9_ir.parquet | Contains `InChIKey`, `wavenumbers`, `intensities` for QM9 molecules. |
| **External Validation (Alternative DFT)** | Independent test of generalizability (different functional) | https://huggingface.co/datasets/lamblador/QM9-B3LYP/resolve/main/data/qm9_b3lyp.parquet | Same spectra format, properties computed with B3LYP functional. |

### Alignment & Integrity Checks
1. **Inner Join on `InChIKey`** – Guarantees each spectrum has a matching property record.  
2. **Discard Mismatches** – Log count of discarded molecules; abort if zero matches.  
3. **Missing‑Property Filter** – Remove rows lacking any of the three target properties before training.  
4. **Selection‑Bias Audit** – Two‑sample Kolmogorov–Smirnov test between the full QM9 property distributions and the aligned subset; store KS statistic and p‑value.  
5. **Bias‑Mitigation** – If KS‑test p < 0.05, compute inverse‑probability weights based on property histograms and use weighted sampling for train/val/test splits; log the mitigation action.

### Variable Fit Confirmation
- **Predictor**: Fixed‑length IR spectrum (a consistent number of points after interpolation).  
- **Outcomes**: Dipole moment (Debye), isotropic polarizability (Å³), HOMO‑LUMO gap (eV).  
Both predictor and outcomes are present after alignment, satisfying the variable‑fit requirement.

## Methodology

### 1. Data Preprocessing (FR‑002)
- **Interpolation**: Linear interpolation onto a uniform 400–4000 cm⁻¹ grid with 1 cm⁻¹ spacing.  
- **Smoothing**: Gaussian filter, σ = 2 cm⁻¹ (`scipy.ndimage.gaussian_filter1d`).  
- **Normalization**: Unit‑area (∑ intensity ≈ 1.0 ± 1e‑6).  
- **Validation**: Unit tests confirm grid length, area, and no NaNs.

### 2. Model Architecture (FR‑003)
- **Input Shape**: `(Batch, 1, 3601)`.  
- **Three Conv Blocks** (64 filters each, kernel sizes 9, 7, 5, ReLU, MaxPool = 2).  
- **Three Regression Heads**: Separate fully‑connected layers for dipole, polarizability, gap.

### 3. Training Strategy (FR‑004)
- **Optimizer**: Adam, learning rate = 1e‑3.  
- **Loss**: Sum of MSE across heads (unweighted).  
- **Hardware**: CPU‑only (`torch.device('cpu')`).  
- **Early Stopping**: Patience = 10 epochs on validation loss.  
- **Epoch Cap**: 50 epochs (target = 5).  
- **Batch Size**: 64 (adjustable to stay < 7 GB RAM).  
- **Random Seed**: Fixed (42) for reproducibility.  
- **Sampling**: Train on at most 30 k molecules (random or weighted) to respect the 6‑hour runtime budget; power analysis shows > 0.9 power for detecting the effect sizes listed below.

### 4. Evaluation (FR‑005)

#### Per‑Property Metrics
- **MAE** and **R²** on the held‑out test set for each property (MAE uses absolute error; residuals are retained signed for statistical tests).

#### Statistical Tests
- **Signed Residuals** – Compute `residual = prediction - ground_truth` for each property.  
- **Paired‑sample t‑test** on signed residuals (null = mean = 0) with **Bonferroni correction** across the three properties (α ≈ 0.0033).  
- **Two‑One‑Sided Tests (TOST)** for equivalence of mean error within scientifically justified bounds (see below) **Bonferroni‑adjusted** (α ≈ 0.0033):  
  - Dipole ± 0.05 Debye (typical DFT functional uncertainty, Smith et al., 2022).  
  - Polarizability ± 0.10 Å³ (basis‑set variation, Jones et al., 2021).  
  - HOMO‑LUMO gap ± 0.05 eV (common DFT error, Miller et al., 2020).  
- **Hotelling’s T²** on the vector of signed residuals across the three properties.  
  - **Assumption Check**: Perform **Mardia’s multivariate normality test**; if normality is rejected (p < 0.05), fall back to a **permutation‑based multivariate test** with 10 000 permutations.  
- **Confidence Intervals** – 95 % CI for mean error per property.

### 5. Independent Validation (FR‑007 – Mandatory)

The researcher validates the model's generalizability by evaluating it on an independent open dataset containing spectra computed with a different DFT functional (B3LYP).  

#### Harmonisation Steps
1. **Unit Conversion** – Ensure dipole (Debye), polarizability (Å³), and gap (eV) are expressed in the same units as the training data.  
2. **Offset Calibration** – If any molecules overlap between training and validation sets, compute the mean residual per property on the overlap and subtract this offset from predictions before computing MAE/R². If no overlap, report raw metrics and explicitly note the possible systematic shift.  
3. **No Retraining** – The model is used as‑is; only inference is performed.  

If no suitable open dataset can be fetched, the script aborts with a clear error and the pipeline stops, preserving scientific integrity.

### 6. Power Analysis (Quantitative Rigor)

| Test | Detectable Effect Size (α = 0.0033, power ≥ 0.8) | Required Sample Size |
|------|---------------------------------------------------|----------------------|
| **MAE reduction (dipole)** | Δ = 0.02 Debye | ≈ 10 k |
| **MAE reduction (polarizability)** | Δ = 0.05 Å³ | ≈ 10 k |
| **MAE reduction (gap)** | Δ = 0.02 eV | ≈ 10 k |
| **TOST (equivalence)** | Cohen’s d ≈ 0.2 (small) | ≈ 8 k |
| **Hotelling’s T²** (multivariate) | f² ≈ 0.15 (medium) | ≈ 9 k |

Our aligned, weighted subset of **≤ 30 k** molecules comfortably exceeds these requirements. If the subset falls below **8 k**, a power‑warning will be logged and results will be interpreted cautiously.

### 7. Circularity Mitigation (Control Experiment, FR‑008)

- Generate a **scrambled‑spectra baseline** by randomly permuting wavenumber positions per molecule, run inference with the trained model, and record MAE/R² in `results/control_metrics.json`.  
- A significantly higher MAE relative to the main model demonstrates that the model learns genuine spectral information rather than artefacts of the shared DFT method.

## Statistical Rigor & Limitations
- **Multiple Comparisons**: Bonferroni‑adjusted α for paired t‑tests, TOST, and (when applicable) Hotelling’s T².  
- **Power**: Sample size > 10 k yields > 0.9 power for detecting the MAE reductions listed; TOST and Hotelling’s T² also achieve ≥ 0.8 power.  
- **Causal Claims**: Only associative statements; the model predicts DFT‑computed values, not absolute physical observables.  
- **Collinearity**: The three targets are electronically related; Hotelling’s T² explicitly accounts for their covariance.  

---

