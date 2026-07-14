# Implementation Plan: Exploring the Potential for Machine Learning to Identify Novel Phase Transitions in Isotropic Systems

**Branch**: `001-gene-regulation` | **Date**: 2026-07-14 | **Spec**: `specs/001-exploring-the-potential-for-machine-lear/spec.md`
**Input**: Feature specification from `/specs/001-exploring-the-potential-for-machine-lear/spec.md`

## Summary

This project implements a CPU-tractable pipeline to detect phase transitions in 2D isotropic spin systems (J1-J2 Heisenberg and XY models) using unsupervised machine learning. The core approach involves generating Monte Carlo simulation data, training a Variational Autoencoder (VAE) with convolutional layers to learn a compressed latent representation, and identifying the critical temperature $T^*$ by detecting a peak in the variance of the reconstruction error or specific latent dimensions. 

**Critical Methodology Update**: To address scientific rigor, the plan replaces Bayesian Change Point Detection (BCPD) with a **Savitzky-Golay smoothing followed by derivative-based peak detection**, as phase transitions in finite systems manifest as smooth peaks, not step functions. Furthermore, the validation strategy uses the **extrapolated critical temperature $T_c(\infty)$** derived from Finite Size Scaling (FSS) of the magnetic susceptibility, rather than the raw finite-size peak, to avoid circular validation.

The implementation is strictly constrained to run within GitHub Actions free-tier limits (limited CPU, ~7 GB RAM, 6 hours).

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `numpy`, `torch` (CPU-only), `scikit-learn`, `scipy`, `pandas`, `matplotlib`, `seaborn`, `pytest`  
**Storage**: Local temporary files (`data/` directory) for raw configurations and processed tensors; no external database.  
**Testing**: `pytest` with `pytest-timeout` to enforce the 6-hour CI limit.  
**Target Platform**: Linux (GitHub Actions `ubuntu-latest` runner).  
**Project Type**: Computational research pipeline / CLI tools.  
**Performance Goals**: Complete data generation (L=16, 24, 32), VAE training (50 epochs), and analysis in < 6 hours on 2 CPU cores. RAM usage < 7 GB.  
**Constraints**: No GPU, no CUDA, no 8-bit quantization. Data must be subsampled or generated on-the-fly to fit memory.  
**Scale/Scope**: L=16 (primary), L=24, L=32 (if feasible for FSS); Temperature range T=0.1 to 3.0; A sufficient number of samples per temperature bin will be collected to ensure statistical robustness. (subject to memory constraints).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | **PASS** | All random seeds will be pinned in `code/`. Data generation scripts will be deterministic. Dependencies pinned in `requirements.txt`. |
| **II. Verified Accuracy** | **PASS** | **Citation Validation Gate**: A pre-execution step runs the `Reference-Validator Agent` to verify all citations in `plan.md` and `research.md` against primary sources. Execution blocks if any citation is unreachable or mismatched. The `validate_citations.py` script is explicitly integrated into Phase 3. |
| **III. Data Hygiene** | **PASS** | **Checksumming**: `generator.py` computes SHA-256 checksums for every raw data file immediately upon generation. Raw data is preserved unchanged; derivations are written to new filenames with derivation logs. |
| **IV. Single Source of Truth** | **PASS** | All figures and statistics in the final report will be generated programmatically from `data/` and `code/`. No hand-typed values. |
| **V. Versioning Discipline** | **PASS** | **Versioning Automation**: A script `code/scripts/update_state.py` will automatically compute content hashes of artifacts and update `state/projects/PROJ-111-exploring-the-potential-for-machine-lear.yaml` upon successful pipeline completion. This is a specific task in Phase 3. |
| **VI. Latent-Space Criticality Validation** | **PASS** | The primary metric is the peak in the variance of the reconstruction error or specific latent dimensions, validated by a diagnostic check for order parameter alignment. BCPD is replaced by peak detection. |
| **VII. Independent Physical Verification** | **PASS** | $T^*$ is validated against the **extrapolated** critical temperature $T_c(\infty)$ derived from Finite Size Scaling (FSS) of magnetic susceptibility, avoiding circular validation against the raw finite-size peak. |

## Project Structure

### Documentation (this feature)

```text
specs/001-exploring-the-potential-for-machine-lear/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Design Artifacts)
    ├── dataset.schema.yaml
    └── latent_schema.schema.yaml
```
*Note on Contracts*: The `contracts/` directory contains schemas defined during the design phase (Phase 1). These schemas serve as **inputs** for the data generation and validation logic in the pipeline, ensuring the generated data adheres to the defined structure. **Task 'Define and write contract schemas' in Phase 1** explicitly creates these files as deliverables.

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Hyperparameters, paths, seeds
├── data/
│   ├── generator.py     # Monte Carlo simulation (Metropolis-Hastings) with checksumming
│   ├── loader.py        # Data loading, preprocessing, and autocorrelation calculation
│   └── utils.py         # Physical observable calculators (Magnetization, Susceptibility, FSS)
├── models/
│   ├── vae.py           # VAE Architecture (ConvEncoder, ConvDecoder)
│   └── training.py      # Training loop, early stopping, loss tracking
├── analysis/
│   ├── latent_analysis.py # Variance calculation, Peak Detection (Savitzky-Golay)
│   └── bootstrap.py     # Resampling for confidence intervals (using independent samples)
├── scripts/
│   ├── update_state.py  # Versioning automation script
│   └── validate_citations.py # Reference-Validator Agent wrapper
├── main.py              # Orchestration script
└── requirements.txt     # Pinned dependencies

tests/
├── test_data_generation.py
├── test_vae_training.py
└── test_analysis.py
```

**Structure Decision**: Single `code/` directory structure selected to maintain simplicity for a research pipeline. Separation of concerns (data, model, analysis) ensures modularity while keeping the codebase lightweight for CPU execution.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Convolutional VAE** | Required to capture spatial correlations in spin configurations. | MLPs fail to capture local spin interactions effectively; 1D CNNs insufficient for 2D lattice topology. |
| **Finite Size Scaling (FSS)** | Required to distinguish true phase transitions from finite-size artifacts and extrapolate to $L \to \infty$. | Single-lattice analysis cannot distinguish between a true transition and a finite-size crossover. |
| **Savitzky-Golay Peak Detection** | Required for identifying the maximum of a smooth, finite-size peak. | Bayesian Change Point Detection (BCPD) assumes step functions and is methodologically unsound for peak-shaped curves. |
| **Autocorrelation Correction** | Required to ensure statistical independence of samples near $T_c$. | Ignoring $\tau_{int}$ leads to underestimated confidence intervals and invalid p-values. |

## Implementation Phases

### Phase 0: Data Generation & Preprocessing (P1)
1.  **Generate Data**: Run Metropolis-Hastings for L=16, L=24, and L=32 (if time permits) across T=0.1 to 3.0.
2.  **Autocorrelation Check**: Calculate integrated autocorrelation time $\tau_{int}$ for magnetization at each T.
3.  **Independent Sampling**: Ensure measurement interval $> 10 \times \tau_{int}$.
4.  **Checksumming**: **`generator.py` computes SHA-256 checksums for every raw data file immediately upon generation.** Record in metadata.
5.  **Preprocessing**: Normalize spins, reshape to `[batch, 3, L, L]`, and split /20 stratified.

### Phase 1: VAE Training & Contract Definition (P2)
1.  **Architecture**: 2 Conv Encoder, 2 Transposed Conv Decoder, Latent Dim=10.
2.  **Contract Definition**: **Task: Define and write contract schemas.** Create `contracts/dataset.schema.yaml` and `contracts/latent_schema.schema.yaml` as deliverables. These serve as inputs for the pipeline.
3.  **Training**: Adam (lr=1e-3), Max a sufficient number of epochs, Early Stopping (patience=5).
4.  **Resource Check**: Monitor RAM (< 7 GB) and Time (< 6 hours). Fail if exceeded.

### Phase 1.5: Finite Size Scaling Protocol (P3)
1.  **Susceptibility Calculation**: Compute $\chi(T)$ for each L.
2.  **Extrapolation**: Fit $T_c(L) = T_c(\infty) + a L^{-1/\nu}$ to determine the thermodynamic limit $T_c(\infty)$.
3.  **Ground Truth Definition**: Set $T_c(\infty)$ as the validation target.

### Phase 2: Latent Space Analysis (P3)
1.  **Metric Calculation**: Compute variance of **reconstruction error** and specific latent dimensions per T. (If mean variance is flat, pivot to error variance).
2.  **Peak Detection**: Apply Savitzky-Golay smoothing and find the maximum of the first derivative.
3.  **Bootstrap**: Resample independent subsamples (1000 iterations) to compute 95% CI for $T^*$.
4.  **Artifact Rejection**: Verify that the peak sharpens with increasing L. If not, flag as artifact.

### Phase 3: Validation & Reporting
1.  **Comparison**: Compare ML-derived $T^*$ with extrapolated $T_c(\infty)$.
2.  **Citation Validation**: **Run `validate_citations.py` to ensure all references are valid.** Block advancement if any fail.
3.  **Versioning**: **Run `update_state.py` to hash artifacts and update state file.**

## Success Criteria

- **SC-001**: The ML-derived $T^*$ matches the extrapolated $T_c(\infty)$ within the 95% confidence interval.
- **SC-002**: The peak in latent variance persists and sharpens with increasing L (FSS consistency).
- **SC-003**: The pipeline completes within 6 hours on 2 CPU cores.
- **SC-004**: All citations are verified by the Reference-Validator Agent.
- **SC-005**: All data files are checksummed and versioned.