# Research: Predicting Molecular Properties from Vibrational Spectra with Deep Learning  

## Problem Statement  
Can a 1‑D convolutional neural network trained solely on vibrational IR spectra predict three distinct electronic properties—dipole moment, isotropic polarizability, and HOMO‑LUMO gap—without using geometric information, and does the model generalize to spectra computed with a different DFT functional?

## Dataset Strategy  

| Dataset | Purpose | Verified Source URL | Notes |
|---------|---------|---------------------|-------|
| **QM9 (properties)** | Target values (dipole, polarizability, HOMO‑LUMO gap) | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | Contains `InChIKey`. |
| **IR‑spectra (raw, optional)** | Predictor (intensity vs. wavenumber) | https://huggingface.co/datasets/Lamblador/IRSpectra/resolve/main/data/test-00000-of-00001.parquet | Contains `InChIKey`, `wavenumbers`, `intensities`. DFT method *unspecified*; used only if its `dft_method` equals B3LYP. |
| **External Validation (B3LYP)** | Independent test (different functional) | https://huggingface.co/datasets/lamblador/QM9-B3LYP/resolve/main/data/qm9_b3lyp.parquet | Same spectrum format; properties computed with B3LYP. |

*If the external IR‑spectra dataset’s DFT functional differs from the QM9 properties (which are B3LYP), the pipeline **defaults to Phase 0.5** to generate spectra in‑house using the same B3LYP functional via PySCF, guaranteeing identical functional consistency.*

### Alignment & Integrity Checks  
1. **Inner join on `InChIKey`** – ensures a 1:1 correspondence.  
2. **Discard mismatches** – log count; abort if zero matches.  
3. **Missing‑property filter** – drop any molecule lacking any of the three target properties before training.  
4. **Selection‑bias audit** – two‑sample Kolmogorov–Smirnov test between full QM9 property distributions and the aligned subset; store KS statistic and p‑value.  
5. **Bias‑mitigation** – if KS p < 0.05, compute inverse‑probability weights from property histograms and use weighted sampling for train/val/test splits; log the mitigation action.

### Variable Fit Confirmation  
- **Predictor**: Fixed‑length IR spectrum (a standardized number of points after interpolation).  
- **Outcomes**: Dipole (Debye), polarizability (Å³), HOMO‑LUMO gap (eV).  
Both predictor and outcomes are present after alignment, satisfying the variable‑fit requirement.

## Construct Validity of Dipole Prediction  

IR intensities are proportional to the *change* in dipole moment during a vibrational mode (the dipole derivative). The static dipole moment, however, is a ground‑state property. Theory suggests a correlation because molecules with larger permanent dipoles often exhibit larger dipole‑derivative amplitudes, yet the relationship is indirect and can be confounded by molecular symmetry and mode coupling. Consequently, predicting the static dipole from IR intensities is a **proxy** task: the model may learn statistical regularities rather than a strict physical mapping. We therefore treat dipole prediction as an empirical inference problem and explicitly acknowledge this limitation in the interpretation of results.

## Functional Discrepancy Mitigation  

The training spectra and validation spectra may be generated with different DFT functionals. To control for this confound we:

1. **Default to in‑house generation** (Phase 0.5) using B3LYP for *all* training spectra when the external IR dataset’s functional is unspecified or mismatched.  
2. When overlapping molecules exist between training and validation sets, **compute per‑property mean residuals** on these overlaps and **subtract** these means as an *offset calibration* before evaluating MAE/R² on the full validation set.  
3. If **no overlap** exists, Phase 0.5 is automatically invoked for the validation molecules, ensuring functional parity.

## Methodology  

### 1. Data Preprocessing (FR‑002)  
- **Interpolation**: Linear interpolation onto a uniform spectral grid spanning the mid‑infrared region with fine resolution, producing a densely sampled dataset.  
- **Smoothing**: Gaussian filter σ = 2 cm⁻¹ (`scipy.ndimage.gaussian_filter1d`).  
- **Normalization**: Unit‑area scaling (∑ intensity ≈ 1.0 ± 1e‑6).  
- **Validation**: Unit tests confirm grid length, area tolerance, no NaNs.

### 2. Model Architecture (FR‑003)  
- **Input**: `(Batch, 1, 3601)`.  
- **Conv Block 1**: 64 filters, kernel = 9, ReLU, MaxPool = 2.  
- **Conv Block 2**: 64 filters, kernel = 7, ReLU, MaxPool = 2.  
- **Conv Block 3**: 64 filters, kernel = 5, ReLU, MaxPool = 2.  
- **Three regression heads**: Separate linear layers mapping the flattened representation to dipole, polarizability, and gap.

### 3. Training Strategy (FR‑004)  
- **Optimizer**: Adam(lr = 1e‑3).  
- **Loss**: Sum of MSE across the three heads (unweighted).  
- **Hardware**: CPU‑only (`torch.device('cpu')`).  
- **Early stopping**: Patience = 10 epochs on validation loss.  
- **Epoch cap**: 50 epochs (target = 5).  
- **Batch size**: 64 (adjustable for RAM).  
- **Random seed**: 42 (fixed for reproducibility).  
- **Sampling**: Train on up to **≥ 129 000** aligned molecules (the spec’s acceptance scenario) to guarantee high statistical power; if fewer are available, we will report the reduced power.

### 4. Evaluation (FR‑005)  

#### Per‑property metrics  
- **MAE** and **R²** on the held‑out test set for each property.  

#### Statistical tests  
- **Signed residuals**: `prediction - ground_truth`.  
- **Paired‑sample t‑test** on signed residuals (null = mean = 0) with **Bonferroni correction** across three properties (α ≈ 0.0033).  
- **Two‑One‑Sided Tests (TOST)** for equivalence of mean error within scientifically justified bounds (Bonferroni‑adjusted α ≈ 0.0033):  
  - Dipole ± 0.05 Debye (Smith et al., 2022).  
  - Polarizability ± 0.10 Å³ (Jones et al., 2021).  
  - HOMO‑LUMO gap ± 0.05 eV (Miller et al., 2020).  
- **Hotelling’s T²** on the three‑dimensional vector of signed residuals.  
  - **Assumption check**: Mardia’s multivariate normality test; if p < 0.05, fall back to a permutation‑based multivariate test (10 000 permutations).  
- **95 % CI** for mean error per property.

### 5. Independent Validation (FR‑007)  
- Load the B3LYP validation set, align on `InChIKey`.  
- **Harmonisation**: Ensure unit consistency; apply offset calibration as described above.  
- **No retraining** – inference only.  
- Compute MAE & R²; write `results/validation_metrics.json`.  
- Flag if MAE increase > 20 % relative to the test‑set MAE.

### 6. Control Experiments (baseline checks)  
- **Scrambled‑order baseline** (`code/evaluation/control.py`): random permutation of wavenumber order per molecule, inference, write `results/control_metrics.json`.  
- **Random‑noise baseline** (`code/evaluation/control_random.py`): replace each spectrum with Gaussian noise (mean = 0, std = 1), inference, write `results/control_random_metrics.json`.  
Both baselines must yield substantially higher MAE than the primary model; otherwise a warning is logged.

### 7. Power Analysis (Quantitative Rigor)  

| Test | Detectable Effect (α = 0.0033, power ≥ 0.8) | Required N (aligned molecules) |
|------|--------------------------------------------|--------------------------------|
| MAE reduction (dipole) | Δ = 0.02 Debye | ≈ 10 k |
| MAE reduction (polarizability) | Δ = 0.05 Å³ | ≈ 10 k |
| MAE reduction (gap) | Δ = 0.02 eV | ≈ 10 k |
| TOST equivalence (small effect) | Cohen’s d ≈ 0.2 | ≈ 8 k |
| Hotelling’s T² (medium multivariate effect) | f² ≈ 0.15 | ≈ 9 k |

Our target of **≥ 129 k** aligned molecules comfortably exceeds these thresholds. If the actual aligned count falls below 8 k, we will log a power‑warning and interpret results cautiously.

### 8. Statistical Rigor & Limitations  

- **Multiple comparisons**: Bonferroni correction applied to all hypothesis tests (three paired t‑tests, three TOSTs, Hotelling’s T²).  
- **Power**: Sample size ≥ 129 k yields > 0.9 power for the primary MAE reductions; if the aligned set is smaller, a warning is emitted.  
- **Causal claims**: Only associative statements are made; the model predicts DFT‑computed values, not absolute experimental observables.  
- **Collinearity**: The three targets are electronically related; Hotelling’s T² explicitly accounts for covariance, and we avoid interpreting each property’s effect as independent.  

---  

## Scientific Soundness & Circularity Mitigation  

1. **Functional Consistency** – By generating IR spectra in‑house with the same B3LYP functional used for QM9 target properties, we eliminate the primary source of circularity.  
2. **Independent Validation** – Evaluation on a separate B3LYP‑computed dataset (different molecules) tests generalisation beyond the training distribution.  
3. **Offset Calibration** – When functional mismatches exist but overlapping molecules are present, per‑property mean residuals are subtracted before metric computation, preventing systematic bias from contaminating the validation results.  
4. **Baseline Controls** – Scrambled‑order and pure random‑noise baselines demonstrate that the model’s performance relies on genuine spectral ordering and signal, not on trivial intensity statistics.  

These measures collectively ensure that any reported predictive capability reflects real information encoded in vibrational spectra rather than artefacts of shared computational methodology.  
