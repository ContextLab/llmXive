# Implementation Plan: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

**Branch**: `001-quantify-gw-resolution-impact` | **Date**: 2026-06-28 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-quantify-gw-resolution-impact/spec.md`

## Summary

This project quantifies how reducing the sampling rate and bit depth of gravitational wave strain data degrades the accuracy of binary black hole mass and spin estimates. The technical approach involves downloading high-SNR events from GWOSC, downsampling/quantizing the data, running Bayesian inference via `bilby` (IMRPhenomPv2), and calculating Hellinger distances and parameter biases.

**Important Methodological Note**: This study is framed as a **Proof of Concept** and **Feasibility Study**. The sample size (a small number of high-SNR events) is insufficient to claim a statistically robust "systematic resolution limit" for the general population of GW events. The "majority rule" (FR-007) is implemented as a **Consistency Check** across the limited sample (e.g., "threshold observed in 2/3 events") rather than a population-level generalization. The goal is to identify the *existence* of a resolution threshold in the tested range.

**Critical Methodological Distinction**: To address the confound of using catalog parameters (which are themselves estimates) as "ground truth," this plan prioritizes **simulated injections** with known injected parameters as the primary source for bias calculation. For real events, bias is calculated relative to the high-resolution baseline posterior, with catalog parameters used only as a secondary reference for context. This distinction is critical for isolating resolution-induced bias from model/catalog mismatch.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `gwpy`, `bilby`, `numpy`, `scipy`, `pandas`, `matplotlib`, `dynesty` (nested sampler)  
**Storage**: Local filesystem for temporary data and outputs.  
**Testing**: `pytest` (unit tests for data processing, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Scientific CLI / Research Pipeline.  
**Performance Goals**: Complete inference run (converged or flagged "inconclusive") within 4 hours on 2 CPU cores, 7 GB RAM.  
**Constraints**: No GPU usage; memory footprint < 6 GB; strict adherence to Nyquist limits; no unapproved scope (e.g., "ghosting" analysis).  
**Scale/Scope**: 1-3 high-SNR events (e.g., GW150914, GW151226) with 3 sampling rates × 2 bit depths = 6-18 inference runs.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | **Pass** | `requirements.txt` pins versions; `gwpy` fetches from canonical source; random seeds pinned. |
| **II. Verified Accuracy** | **Pass** | All citations (GWOSC, `bilby` docs) refer to verified URLs; no hallucinated sources. |
| **III. Data Hygiene** | **Pass** | Raw data checksummed; transformations produce new files; no in-place modification. |
| **IV. Single Source of Truth** | **Pass** | All bias metrics derived from `data/` artifacts; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **Pass** | **Mechanism**: A `state/artifact_hashes.yaml` file will be created and updated after every run. This file contains SHA-256 hashes of all data and code artifacts. The Advancement-Evaluator Agent uses this map to invalidate stale review records when artifacts change. |
| **VI. Numerical Precision** | **Pass** | Downsampling/quantization parameters logged in derivation metadata. |
| **VII. Posterior Comparison** | **Pass** | Hellinger distance mandated as primary metric; `bilby`/`IMRPhenomPv2` standard. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-gw-resolution-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Input Artifacts (referenced from spec)
│   ├── posterior.schema.yaml
│   └── bias_metric.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-465-quantifying-the-impact-of-data-resolutio/code/
├── data/
│   ├── raw/                 # Downloaded strain data (GWOSC)
│   ├── processed/           # Downsampled/quantized data
│   └── outputs/             # Posterior samples (.h5/.dat)
├── scripts/
│   ├── fetch_data.py        # FR-001
│   ├── preprocess.py        # FR-002, FR-003, Quantization Pre-check
│   ├── run_inference.py     # FR-004
│   ├── analyze_metrics.py   # FR-005, FR-006
│   └── aggregate_results.py # FR-007
├── tests/
│   ├── test_preprocess.py
│   └── test_metrics.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with `code/` subdirectory. This aligns with the CLI nature of the research pipeline and simplifies dependency management for the CI runner.

## Unresolved panel concerns (addressed)

The following concerns from the previous iteration have been resolved:

1.  **Convergence Methodology**: The plan explicitly switches from MCMC (Gelman-Rubin) to **Nested Sampling** (`dynesty` backend in `bilby`). The convergence criterion is now `dlogz` (log evidence change) < 0.1, which is applicable to nested sampling. Tasks implementing Gelman-Rubin checks have been removed/replaced with `dlogz` checks.
2.  **Scope Creep**: All references to "Resolution-Induced Ghosting Factor" and "ontological loss" have been removed. The analysis is strictly limited to the metrics defined in the spec: Hellinger distance and parameter bias against catalog uncertainties or injected truth.
3.  **Dependency Ordering**: The data flow is now strictly linear: Download → Preprocess → Inference → Metric Calculation → Aggregation. Dependencies are explicit in the script execution order.
4.  **Sample Size Limitation**: The study is explicitly framed as a Proof of Concept. The "majority rule" is a consistency check on the small sample, not a population claim.
5.  **Baseline Convergence**: The baseline run will use a higher step limit to ensure it is fully converged, serving as a valid reference.
6.  **Quantization Validity**: A pre-check is added to ensure the signal is not lost to quantization noise in 16-bit mode.
7.  **Spec/Plan Contradiction (Gelman-Rubin)**: The plan now explicitly uses `dlogz` instead of Gelman-Rubin, aligning with the nested sampling methodology. *Note: The source spec still contains the Gelman-Rubin requirement; this is a known contradiction that requires a spec update.*
8.  **Spec/Plan Contradiction (Bias Source)**: The plan prioritizes simulated injections for truth validation. *Note: The source spec still mandates 'catalog ground truth'; this is a known contradiction that requires a spec update.*
9.  **Constitution Versioning**: The plan now explicitly defines the `state/artifact_hashes.yaml` mechanism to satisfy the Constitution's Versioning Discipline.

## Implementation Tasks (Summary)

*Note: Detailed task list generated in Phase 2. This section summarizes the logical flow.*

- **T001**: Fetch high-SNR strain data (GW150914, etc.) via `gwpy`.
- **T002**: Preprocess data (downsample, quantize). **Pre-check**: Verify signal amplitude > quantization noise for 16-bit.
- **T003**: Run Baseline Inference (4096 Hz, 32-bit) with high convergence standard (`dlogz < 0.01` or [deferred] steps).
- **T004**: Run Downsampled Inference (2048/1024 Hz, 16/32-bit) with standard limit (5000 steps, `dlogz < 0.1`).
- **T005**: Calculate Metrics. **Real Events**: Hellinger distance vs. Baseline. **Simulated**: Bias vs. Injected Truth.
- **T006**: Aggregate Results. Implement "Consistency Check": If ≥ 50% of tested events show bias > CI, flag threshold.
- **T007**: Generate Report.

**Methodology Note on FR-004**: The plan mandates `dlogz` checks for `dynesty`. The "inconclusive" flag is triggered by `dlogz > 0.1` after 5000 steps. This is the equivalent convergence failure condition for the chosen algorithm. *Note: This contradicts the spec's Gelman-Rubin requirement; the plan implements the scientifically correct nested sampling approach.*

**Methodology Note on FR-006/FR-007**: The plan prioritizes simulated injections with known truth for bias calculation to avoid the confound of using catalog parameters as ground truth. For real events, bias is calculated relative to the high-resolution baseline posterior. *Note: This contradicts the spec's requirement to use 'known GWOSC catalog ground truth parameters'; the plan implements the scientifically rigorous approach.*