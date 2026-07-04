# Implementation Plan: Quantifying the Impact of Data Compression on Gravitational Wave Event Reconstruction

**Branch**: `[001-compression-impact-gw-reconstruction]` | **Date**: 2024-01-15 | **Spec**: `specs/001-compression-impact-gw-reconstruction/spec.md`
**Input**: Feature specification from `/specs/001-compression-impact-gw-reconstruction/spec.md`

## Summary

This feature implements a computational pipeline to quantify how lossless (gzip, LZ4, bzip2) and lossy (JPEG2000, floating-point quantization) compression techniques affect the accuracy of gravitational wave (GW) signal reconstruction and parameter estimation for compact binary coalescence (CBC) events. 

The approach involves two distinct workflows:
1.  **Real Events (GWOSC)**: Acquire validated data, apply compression, run LALInference, and measure **Posterior Shift** (KL divergence) to assess stability.
2.  **Simulated Injections**: Generate synthetic signals with known ground truth, apply compression, run LALInference, and measure **Parameter Bias** (MAE) against the known truth.

The pipeline explicitly distinguishes between "instability" (shift in distribution for real events) and "bias" (systematic error for injections).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: 
- `gwosc` (for API access)
- `lalsuite` (LALInference CPU mode, `lalapps`)
- `numpy` (for custom floating-point quantization: 16/8/4-bit)
- `glymur` (for JPEG2000 support on spectrograms)
- `scipy` (for signal processing, spectrograms, statistical tests)
- `scikit-learn` (for ANOVA, power analysis)
- `pandas`, `pyyaml`, `pytest`
**Storage**: Local file system (`data/raw`, `data/processed`, `data/derived`); no database.  
**Testing**: `pytest` with contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM).  
**Project Type**: CLI/Research Pipeline.  
**Performance Goals**: 
- Complete analysis of ≥12 real events and 50 simulated injections within 6 hours.
- Memory usage <6GB per job.
- **MCMC Convergence**: Minimum 50,000 iterations with Gelman-Rubin convergence check (R-hat < 1.1).
**Constraints**: 
- No GPU/CUDA; no 8-bit/4-bit quantization libraries requiring bitsandbytes.
- JPEG2000 applied to **spectrograms** (time-frequency representation), not raw 1D time series.
- Bias calculation for injections uses **ground-truth parameters** and **theoretical SNR** exclusively.
- SNR degradation > 5% threshold triggers "unacceptable" classification.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Reproducibility | PASS | Plan mandates pinned `requirements.txt`, random seeds, and checksums for all data. |
| II. Verified Accuracy | PASS | Plan restricts dataset citations to verified URLs (GWOSC O3a/O3b catalogs) and cited injection models. |
| III. Data Hygiene | PASS | Plan enforces read-only raw data, checksummed derivatives, and no in-place modification. |
| IV. Single Source of Truth | PASS | All figures/stats will trace to `data/` rows and `code/` blocks; no hand-typed numbers. |
| V. Versioning Discipline | PASS | Artifacts will carry content hashes; state updated on change. |
| VI. Compression Fidelity | PASS | Plan explicitly lists required algorithms/levels; deviations require provenance logging. |
| VII. Parameter-estimation Integrity | PASS | Plan mandates LALInference CPU-mode. **Note**: While Constitution mentions "paired t-tests", this plan uses **Repeated-measures ANOVA** to handle >2 groups (multiple compression levels) as required by SC-004. Pairwise t-tests with Bonferroni correction will be used for post-hoc analysis if ANOVA is significant. |

## Project Structure

### Documentation (this feature)

```text
specs/001-compression-impact-gw-reconstruction/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── gw-event.schema.yaml
│   └── compression-result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── 01_data_acquisition.py      # GWOSC download & validation
├── 02_compression_engine.py    # Lossless/Lossy application (numpy quantization, glymur JPEG2000)
├── 03_simulation.py            # Synthetic injection generation (50 injections, O3b model)
├── 04_parameter_estimation.py  # LALInference CPU wrapper (50k iterations, convergence check)
├── 05_analysis.py              # KL divergence (real), MAE Bias (injections), ANOVA
├── 06_visualization.py         # Plot generation
└── requirements.txt            # Pinned dependencies

data/
├── raw/                        # Downloaded GWOSC files (checksummed)
├── processed/                  # Compressed/Decompressed waveforms & spectrograms
└── derived/                    # Posteriors, statistics, plots

tests/
├── contract/                   # Schema validation tests
└── integration/                # End-to-end pipeline tests
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data processing and analysis steps, minimizing I/O overhead on the constrained CI runner.

## Implementation Phases

### Phase 0: Data Acquisition & Validation
- **Goal**: Download ≥15 GWOSC events, validate completeness (≥95% fields), retain ≥12.
- **Action**: Use `gwosc` API to fetch O3a/O3b catalog events.
- **Validation**: Check for `strain_h_plus`, `strain_h_cross`, `metadata` (mass, distance, spin).
- **Output**: `data/raw/validated_events.json` with checksums.

### Phase 1: Simulation & Ground Truth
- **Goal**: Generate **50** simulated CBC injections with known ground truth.
- **Action**: Use `lalsimulation` with **O3b CBC population model** parameters.
- **Output**: `data/raw/injections_ground_truth.csv` (mass, distance, spin, theoretical SNR).

### Phase 2: Compression Application
- **Goal**: Apply compression to both real and simulated waveforms.
- **Lossless**: gzip, LZ4, bzip2 (levels 1-9).
- **Lossy**: 
  - Floating-point quantization: 16-bit, 8-bit, 4-bit (using `numpy` casting).
  - JPEG2000: Convert strain to **spectrogram** (time-frequency), compress, reconstruct, inverse transform.
- **Validation**: Check bit-identical for lossless; compute MSE for lossy.
- **Output**: `data/processed/compressed_events/` with metadata.

### Phase 3: Parameter Estimation (LALInference)
- **Goal**: Run CPU-mode LALInference on original and compressed data.
- **Configuration**: 
 - Minimum **[deferred]** MCMC iterations.
  - **Convergence Check**: Gelman-Rubin (R-hat < 1.1). If failed, exclude event from bias analysis.
  - CPU-only mode (`--cpu` flag).
- **Output**: `data/derived/posterior_samples/` (`.txt` or `.hdf5` files).

### Phase 4: Analysis & Statistics
- **Goal**: Compute metrics and test hypotheses.
- **Metrics**:
  - **Real Events**: KL divergence between original and compressed posteriors (measures **instability**).
  - **Injections**: Mean Absolute Error (MAE) of estimated parameters vs. **ground truth** (measures **bias**).
  - **SNR**: Degradation % vs. theoretical SNR (for injections).
- **Statistics**:
  - **Repeated-measures ANOVA** on MAE (injections) and KL (real) across compression methods.
  - **Multiple Comparison Correction**: Bonferroni or FDR.
  - **Classification**: SNR degradation ≤ 5% → "Acceptable"; > 5% → "Unacceptable".
- **Output**: `data/derived/stats.json`, `data/derived/plots/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Separate simulation module | Required for independent ground truth (US-4) to distinguish bias from noise. | Cannot rely solely on GWOSC posteriors which are themselves estimates with uncertainty. |
| Statistical correction (Bonferroni/FDR) | Required by SC-004 for multiple comparisons across parameters/methods. | Uncorrected p-values would inflate Type I error rates, violating scientific rigor. |
| Spectrogram for JPEG2000 | JPEG2000 is 2D; GW strain is 1D. Spectrogram provides a domain-appropriate 2D representation. | Direct 1D application is a category error; reshaping introduces undefined artifacts. |
| [deferred] MCMC iterations | Required for posterior convergence (R-hat < 1.1) to ensure bias is not sampling noise. | [deferred] iterations often fail to converge for CBC parameters, confounding bias with sampling error. |
| 50 Simulated Injections | Required for statistical power to detect bias across the parameter space. | A small number of injections are insufficient to generalize findings or cover the O3b population range.. |
| Glymur for JPEG2000 | `Pillow` has limited JPEG2000 support; `glymur` is the standard Python library. | `Pillow` often requires `openjpeg` system libs and fails on complex 1D-to-2D transformations. |
| Numpy Quantization | No dedicated library for 4/8/16-bit float quantization; `numpy` is robust and standard. | Custom implementation ensures exact bit-depth control without external dependencies. |