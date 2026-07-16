# Implementation Plan: Quantifying the Impact of Data Resolution on Gravitational Wave Signal Detection

**Branch**: `001-gene-regulation` | **Date**: 2025-05-15 | **Spec**: `specs/001-quantifying-the-impact-of-data-resolutio/spec.md`
**Input**: Feature specification from `/specs/001-quantifying-the-impact-of-data-resolutio/spec.md`

## Summary

This project quantifies the sensitivity loss and computational savings achieved by down-sampling gravitational wave (GW) strain data. The technical approach involves generating non-spinning Binary Black Hole (BBH) waveforms at a high native sampling rate., applying anti-aliasing FIR filters with explicit amplitude correction, and systematically down-sampling to multiple frequencies including, 512, and 256 Hz. These signals are injected into real LIGO/Virgo noise segments from GWOSC. The pipeline computes matched-filter SNR and re-weighted SNR ($\hat{\rho}$) for each injection using resolution-matched template banks and Power Spectral Densities (PSDs). The analysis calculates detection probabilities and profiles CPU/memory usage. Statistical significance of SNR degradation is assessed primarily via the Jonckheere-Terpstra test for monotonic trends, with Welch's t-tests (adjacent pairs only) or Mann-Whitney U tests as secondary checks.

## Technical Context

**Language/Version**: Python 3.x  
**Primary Dependencies**: `pycbc` (CPU-only), `scipy`, `numpy`, `pandas`, `gwosc`, `pytest`, `memory-profiler`, `scikit-learn`  
**Storage**: Local file system (`data/raw/`, `data/processed/`, `data/profiling/`)  
**Testing**: `pytest` (unit and integration), `pytest-cov`  
**Target Platform**: Linux (GitHub Actions free-tier: A minimal compute configuration consisting of a low-core CPU and limited RAM will be provisioned to support the research question. The method involves deploying this configuration to evaluate system performance under constrained resources. References: DOI/10.1234/example., no GPU)  
**Project Type**: CLI / Research Pipeline  
**Performance Goals**: Complete injection/analysis of a statistically powered subset within 6 hours; memory < 6GB.  
**Constraints**: No GPU acceleration; strict anti-aliasing; statistical power ≥ 0.8 for [deferred] SNR degradation (via pilot); Bonferroni correction for adjacent pairwise comparisons only.
**Scale/Scope**: resolution levels; component masses in the stellar-mass range (M⊙); distances –500 Mpc; sample size determined by a two-stage pilot study.

> **Compute Feasibility Note**: The plan explicitly avoids GPU dependencies. `pycbc` will be configured to use CPU vectorization only. Data loading is streamed or chunked to respect the available RAM limit.

### Memory Enforcement
The pipeline includes a runtime memory monitor. If peak memory usage exceeds **6GB** during any batch processing step, the current batch is aborted, the job exits with code `1` (Memory Limit Exceeded), and a detailed log is written to `data/profiling/memory_error.log`. This prevents silent degradation or hanging processes and ensures the CI job fails fast.

### Statistical Rigor & Power Analysis Strategy
To satisfy **FR-003** (power ≥ 0.8 for [deferred] SNR degradation) and address the lack of prior variance data:
1.  **Assumed Variance**: The plan assumes a conservative relative standard deviation of **$\sigma_{rel} = 0.05$** for SNR degradation in the pilot phase.
2.  **Two-Stage Pilot**:
    *   **Stage 1**: Execute a pilot injection run with **N=20** injections per resolution level.
    *   **Stage 2**: Calculate the empirical standard deviation ($\sigma_{emp}$) from the pilot.
        *   If $\sigma_{emp} > 0.05$, recalculate the required $N$ using the larger variance.
        *   If $\sigma_{emp} \le 0.05$, proceed with $N=20$ (conservative) or a reduced $N$ if time permits.
    *   **Execution**: Run the full study with the finalized $N$ (capped at a reasonable limit per level due to 6h CI limit).
3.  **Stratification**: All power calculations and statistical tests are performed within **SNR bins** (e.g., 8-12, 12-20, >20) to ensure validity across signal strengths, as SNR variance is signal-dependent.

### Filter Confound Control (Causal Validity)
To isolate resolution loss from filter distortion:
1.  The theoretical frequency response $H(f)$ of the FIR filter is calculated for each target resolution.
2.  The injected waveform amplitude is pre-scaled by $1/|H(f_{peak})|$ before injection.
3.  This ensures that any observed SNR degradation is due to the loss of high-frequency information (resolution), not the filter's attenuation.

### Contract Validation
All output data (injection results, detection metrics) are validated against the JSON schemas defined in `contracts/` **immediately before writing to disk**.
*   `injection.py` calls `validate_schema()` on every injection result row.
*   `analysis.py` calls `validate_schema()` on every aggregated metric row.
*   `test_schemas.py` asserts that these validation calls are triggered and that schema violations raise exceptions.

### Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` pins versions; `config.py` sets `global_seed=42` (overridable via CLI); GWOSC fetchers use canonical API. |
| **II. Verified Accuracy** | **Pass** | Citations for `pycbc` methods and GWOSC data sources will be validated against primary docs via `ReferenceValidator`. |
| **III. Data Hygiene** | **Pass** | All derived files (down-sampled, injected) will have SHA256 checksums recorded in `state/` via `data-hygiene.sh`. |
| **IV. Single Source of Truth** | **Pass** | All SNR/Detection metrics derived solely from `data/processed/injections.csv` (validated against schema). |
| **V. Versioning Discipline** | **Pass** | Artifact hashes updated on every pipeline run; `updated_at` timestamp managed by state agent. |
| **VI. Resolution Integrity** | **Pass** | Anti-aliasing filter parameters (cutoff, type, **transfer function correction**) and resulting sampling rates logged in metadata. |
| **VII. Computational Efficiency** | **Pass** | Wall-clock and memory profiling scripts integrated into the main pipeline; outputs saved to `data/profiling/`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantifying-the-impact-of-data-resolutio/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── injection.schema.yaml
    └── detection_metric.schema.yaml
```

### Source Code (repository root)

```text
src/
├── config.py            # Global seeds, paths, resolution targets
├── waveform_gen.py      # FR-001: BBH generation (pycbc)
├── downsample.py        # FR-002: Anti-aliasing filter, resampling, & amplitude correction
├── injection.py         # FR-003: Noise loading & signal injection (validates schema)
├── matched_filter.py    # FR-004, FR-008: SNR & re-weighted SNR calculation
├── analysis.py          # FR-005, FR-007: Detection prob, Jonckheere-Terpstra, t-tests (validates schema)
├── profiler.py          # FR-006: CPU/Memory profiling wrapper
└── main.py              # Orchestration: Data -> Downsample -> Inject -> Analyze

tests/
├── unit/
│   ├── test_waveform_gen.py
│   ├── test_downsample.py
│   └── test_matched_filter.py
├── integration/
│   └── test_pipeline.py
└── contract/
    └── test_schemas.py  # Validates output against contracts/

data/
├── raw/                 # GWOSC noise segments (cached)
├── processed/           # Down-sampled waveforms, injection logs
└── profiling/           # Resource usage logs
```

**Structure Decision**: Single-project CLI structure selected to minimize overhead and simplify data passing between stages (generation -> injection -> analysis) within the 6-hour CI limit.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Jonckheere-Terpstra Test** | SC-001 requires testing for a monotonic trend across ordered groups. | Pairwise t-tests do not directly test the ordered hypothesis and lose power after correction. |
| **Re-weighted SNR** | FR-008 requires $\hat{\rho}$ to mitigate glitch influence, standard in LIGO/Virgo. | Raw SNR is insufficient for robust detection probability (SC-002) in real noise environments. |
| **Anti-aliasing FIR + Correction** | FR-002 mandates specific filter cutoffs; filter attenuation must be removed to isolate resolution loss. | Naive decimation aliases noise; uncorrected filter attenuation confounds resolution loss with filter distortion. |
| **Resolution-Matched Template Bank** | Scientific Soundness: SNR is a function of template match. | Using a Hz template on Hz data introduces mismatch error, invalidating the degradation metric. |
| **PSD Re-estimation** | Scientific Soundness: PSD is sampling-rate dependent. | Using a 4096Hz PSD on 256Hz data yields mathematically incorrect SNR values. |
| **SNR Stratification** | Methodology: SNR variance depends on signal strength. | Aggregating all SNRs obscures degradation effects in low-SNR regimes. |
| **Mann-Whitney U Fallback** | Scientific Soundness: SNR is non-Gaussian at low values. | Welch's t-test assumes normality; Mann-Whitney U is robust for non-normal distributions. |