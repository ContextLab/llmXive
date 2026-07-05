# Research: Predicting Molecular Properties from Vibrational Spectra with Deep Learning

## Problem Statement

Can a 1-D Convolutional Neural Network (CNN) trained on vibrational IR spectra accurately predict three distinct molecular electronic properties—dipole moment, isotropic polarizability, and HOMO-LUMO gap—without explicit access to molecular geometry or quantum mechanical calculations during inference?

## Dataset Strategy

The project relies on two primary data sources: the QM9 dataset for molecular properties and a corresponding IR-spectra dataset.

| Dataset | Purpose | Source URL | Verification Status |
|---------|---------|------------|---------------------|
| **QM9 (Properties)** | Source for Dipole, Polarizability, HOMO-LUMO gap (DFT computed). | https://huggingface.co/datasets/lisn519010/QM9/resolve/main/data/full-00000-of-00001-e217b6ecfbeb7149.parquet | Verified (Parquet) |
| **IR-Spectra** | Source for vibrational absorption intensities. | https://huggingface.co/datasets/Lamblador/IRSpectra/resolve/main/data/test-00000-of-00001.parquet | Verified (Parquet) |
| **QM9-IR** | *Note:* The spec mentions "QM9-IR" as a single dataset, but **no verified source** exists for a combined "QM9-IR" dataset in the provided list. | **NO verified source found** | **Gap Identified**: The implementation MUST align the separate QM9 and IR-Spectra datasets via InChIKey. |

### Alignment Strategy & Data Integrity
Since a pre-aligned "QM9-IR" dataset is not available in the verified sources, the `data/download.py` and `data/preprocess.py` scripts will:
1. Load the QM9 properties dataset.
2. Load the IR-Spectra dataset.
3. **DFT Method Verification**: Check metadata for DFT functional/basis set. If the IR-Spectra source uses a different functional than QM9 (B3LYP/6-31G*), flag the dataset as a "Domain Shift" candidate rather than a direct training source.
4. Perform an inner join on the `InChIKey` column.
5. **Coverage Audit**: Compute Kolmogorov-Smirnov (KS) statistics comparing the distribution of `mu`, `alpha`, and `gap` between the full QM9 set and the aligned subset. Report any significant selection bias.
6. Discard any molecules missing a match in either dataset (as per US-1, Edge Case 3).
7. Log the count of discarded samples.

### Variable Fit Check
- **Required Predictors**: IR Spectrum (intensity vs. wavenumber).
- **Required Outcomes**: Dipole Moment, Polarizability, HOMO-LUMO Gap.
- **Fit**: The QM9 dataset contains the required electronic properties. The IR-Spectra dataset contains the required spectral data. The alignment via InChIKey ensures the predictor and outcome belong to the same molecule.
- **Caveat**: If the IR-Spectra dataset lacks coverage for the full QM9 set (e.g., only <10% overlap), the effective sample size will be reduced. The plan includes a "Data Scarcity Warning" to scale down model complexity or report power limitations if the intersection is too small.

## Methodology

### 1. Data Preprocessing (FR-002)
- **Interpolation**: Raw spectra will be interpolated to a fixed grid of uniformly spaced points covering the spectral range from the lower to the upper bound of the relevant infrared region.
- **Smoothing**: Gaussian smoothing with σ = 2 cm⁻¹ to reduce high-frequency noise.
- **Normalization**: Unit area normalization (integral of spectrum = 1) to remove intensity scaling effects.
- **Validation**: Check for NaNs or infinite values post-processing; discard corrupted entries.
- **Artifact Check**: `tests/test_preprocessing.py` will verify that interpolation does not introduce frequency shifts or intensity distortions compared to the original grid.

### 2. Model Architecture (FR-003)
- **Type**: 1-D Convolutional Neural Network.
- **Input**: Tensor of shape `(Batch, 1, 3601)`.
- **Blocks**: Three convolutional blocks with varied kernel sizes, followed by max-pooling.
- **Heads**: Three separate fully connected regression heads for:
  1. Dipole Moment
  2. Polarizability
  3. HOMO-LUMO Gap
- **Loss**: Sum of Mean Squared Errors (MSE) for the three heads (weighted or unweighted as per initial experiments).

### 3. Training Strategy (FR-004)
- **Optimizer**: Adam (lr=1e-3).
- **Hardware**: CPU-only (no CUDA).
- **Precision**: Standard float32 (no 8-bit quantization).
- **Early Stopping**: Patience=10 epochs based on validation loss.
- **Max Epochs**: 50 (target 5).
- **Batch Size**: Tuned to fit within 7GB RAM (likely 32 or 64).
- **Seeding**: Fixed random seed for reproducibility (Constitution Principle I).
- **Runtime Enforcement**: A `timeout` wrapper (6 hours) will terminate the process if exceeded (FR-006).

### 4. Evaluation (FR-005, FR-007)
- **Metrics**: MAE and R² for each property.
- **Statistical Test (Per Property)**:
  - **Replaced**: Paired-sample t-test for "mean error = 0" (statistically guaranteed to reject with large N, scientifically meaningless).
  - **Adopted**: **Two One-Sided Tests (TOST)** for equivalence. We test if the mean error is within a scientifically meaningful threshold (e.g., ±0.1 Debye). This assesses *practical significance* rather than trivial non-zero bias.
  - **Confidence Intervals**: 95% CI for mean error will be reported.
- **Multivariate Error Analysis**:
  - **Hotelling's T-squared test** will be performed on the joint error vector (dipole, polarizability, gap) to account for the correlation between these properties. This addresses the multivariate nature of the error structure.
- **Independent Validation**:
  - **Verification**: Check the DFT functional of any candidate validation dataset (e.g., `dft23-full`).
  - **If Different Functional**: Use as "Physical Generalizability" test. Compare MAE against test set (≤20% tolerance).
  - **If Same Functional**: Reclassify as "Hold-out Test Set". Do not claim "physical generalizability".
  - **Fallback (No External Data)**: If no verified external dataset exists, perform a **Domain Shift Simulation** (e.g., adding Gaussian noise to spectra or shifting wavenumbers) to test model robustness. Report this as the "Generalizability" metric, acknowledging the limitation of lacking physical external validation.

## Statistical Rigor & Limitations

- **Multiple Comparisons**: Three distinct TOSTs are performed (one per property). Bonferroni correction will be applied to the equivalence bounds if necessary, or the joint multivariate test (Hotelling's) will be used as the primary significance test.
- **Sample Size / Power**: The effective sample size depends on the intersection of QM9 and IR-Spectra. A power analysis will be deferred to the implementation phase, but the large expected N (>10k) suggests high power for detecting *practical* equivalence.
- **Causal Claims**: The model predicts DFT values, not absolute physical truth. Claims will be framed as "association between spectral features and DFT-computed properties."
- **Collinearity**: Dipole moment and polarizability are related electronic properties. The model treats them as independent outputs; however, the research will acknowledge that spectral features encoding one may correlate with the other. The multivariate test (Hotelling's T²) explicitly models this dependency.
- **Selection Bias**: The KS-test audit will detect if the aligned subset is systematically different from the full QM9 population. If bias is detected, it will be reported as a limitation.

## Compute Feasibility Plan

- **Memory**: The 3601-feature input is small. A batch size of 64 with float32 tensors will consume < 1GB RAM for data, leaving ample room for the model and Python overhead.
- **Runtime**: 1-D CNNs are computationally efficient. Training 50 epochs on 130k samples on a 2-core CPU should complete within 2-4 hours, well under the 6-hour limit. The `timeout` wrapper ensures strict adherence.
- **Libraries**: `torch` CPU wheels, `scikit-learn`, `pandas` are all compatible with the free-tier runner.