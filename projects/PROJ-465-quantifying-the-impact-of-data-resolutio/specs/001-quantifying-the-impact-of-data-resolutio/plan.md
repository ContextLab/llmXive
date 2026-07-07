# Implementation Plan: Quantifying the Impact of Data Resolution on Gravitational Wave Parameter Estimation

**Branch**: `001-quantify-gw-resolution-impact` | **Date**: 2026-06-28 | **Spec**: `specs/001-quantify-gw-resolution-impact/spec.md`
**Input**: Feature specification from `specs/001-quantify-gw-resolution-impact/spec.md`

## Summary

This project quantifies how reducing sampling rates and bit depths degrades the accuracy of binary black hole mass and spin estimates. The technical approach involves downloading high-SNR GWOSC strain data, downsampling/quantizing it, running a `bilby` Bayesian inference pipeline with `IMRPhenomPv2` waveforms using `dynesty` (nested sampling), and calculating Hellinger distances (divergence) and consistency deviations against baseline estimates. For simulated data, absolute bias against injected truth is calculated. The implementation is constrained to CPU-only execution on GitHub Actions free-tier runners.

**Note on Spec Contradiction**: The source spec (Edge Cases) requires excluding events where posterior width > 50% of prior width. This plan implements the *corrected* methodology (analyzing width increase as a metric) to avoid selection bias, as mandated by the methodology panel. The spec is flagged for amendment to align with this corrected approach.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `gwpy`, `bilby`, `dynesty`, `scipy`, `numpy`, `pandas`, `matplotlib`, `h5py`
**Storage**: Local file system (`data/` for raw/derived, `results/` for posteriors)
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for downsampling logic)
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7 GB RAM, no GPU)
**Project Type**: CLI / Research Pipeline
**Performance Goals**: Full inference pipeline (downsampling + nested sampling) must complete within 6 hours.
**Constraints**: No GPU usage; memory usage must stay under a feasible limit; data volume limited to < 100 MB per event.
**Scale/Scope**: 1-3 high-SNR events (e.g., GW150914) tested across 3 sampling rates and 2 bit depths.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Pass** | `requirements.txt` will pin all versions. `gwpy` fetches from canonical GWOSC source. Random seeds pinned in `code/`. |
| **II. Verified Accuracy** | **Pass** | All citations (GWOSC, Bilby, IMRPhenomPv2 papers) will be validated against primary sources before inclusion in `research.md`. |
| **III. Data Hygiene** | **Pass** | Raw data checksums recorded in `state/`. Derivations (downsampled files) written to new filenames with metadata logs. |
| **IV. Single Source of Truth** | **Pass** | Results aggregation script will read directly from `results/` posterior files; no hand-typed numbers in `paper/`. |
| **V. Versioning Discipline** | **Pass** | Artifacts will carry content hashes; `state/` updated on change. |
| **VI. Numerical Precision** | **Pass** | `scipy.signal.decimate` and quantization parameters logged in derivation files. |
| **VII. Posterior Comparison** | **Pass** | Hellinger distance used as primary divergence metric; `bilby` `IMRPhenomPv2` enforced. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-gw-resolution-impact/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── posterior.schema.yaml
│   └── bias_metric.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-465-quantifying-the-impact-of-data-resolutio/
├── code/
│   ├── __init__.py
│   ├── download.py          # GWOSC fetch via gwpy
│   ├── process.py           # Downsampling & quantization
│   ├── infer.py             # Bilby inference runner (dynesty)
│   ├── metrics.py           # Hellinger & Consistency Deviation calculation
│   ├── aggregate.py         # Trend identification
│   └── requirements.txt
├── data/
│   ├── raw/                 # Original GWOSC files (checksummed)
│   └── derived/             # Downsampled/quantized files
├── results/
│   ├── posteriors/          # .h5 output files
│   └── metrics/             # JSON/CSV bias reports
└── tests/
    ├── contract/            # Schema validation tests
    ├── unit/                # Logic tests (downsampling, metrics)
    └── integration/         # End-to-end pipeline test
```

**Structure Decision**: Single project structure selected to minimize overhead for a research pipeline. `code/` contains modular scripts for distinct phases (download, process, infer, metric, aggregate) to ensure reproducibility and isolation.

## Unresolved Concerns Resolution

**Concern**: Spec.md FR-004 requires flagging a run as 'inconclusive' if the Gelman-Rubin statistic >= 1.01 OR if the 5000-step hard limit is reached. The methodology has switched to `dynesty` (nested sampling) where Gelman-Rubin is inapplicable.

**Resolution**: The `infer.py` module (Phase 1) will explicitly implement the logic for `dynesty`:
1. Run nested sampling with `bilby` using `dynesty` sampler.
2. Check convergence via `dlogz` (evidence tolerance) threshold (e.g., a suitable small value).
3. If `dlogz` > threshold after max iterations, set `status = "inconclusive"`.
4. Log this status in the posterior file metadata and the run log.
5. The `aggregate.py` script will treat "inconclusive" runs as excluded from bias calculations but included in the "threshold identification" count (e.g., "Threshold reached where 50% of runs are inconclusive or biased").

**Concern**: Spec.md Edge Cases requires excluding events with wide posteriors. Methodology dictates analyzing width increase to avoid bias.

**Resolution**: The `aggregate.py` and `metrics.py` modules will calculate the Posterior-to-Prior Ratio as a primary metric. The exclusion logic from the spec is **not implemented**; instead, the plan flags the spec for amendment to reflect the corrected methodology.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **N/A** | No violations identified. | N/A |