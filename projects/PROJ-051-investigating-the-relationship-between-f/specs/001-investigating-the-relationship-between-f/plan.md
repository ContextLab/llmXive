# Implementation Plan: Fractal Dimension and Energy Dissipation in Turbulent Flows

**Branch**: `001-fractal-dimension-turbulence` | **Date**: 2024-01-15 | **Spec**: `specs/001-fractal-dimension-turbulence/spec.md`
**Input**: Feature specification from `/specs/001-fractal-dimension-turbulence/spec.md`

## Summary

This project implements a computational pipeline to investigate the relationship between the fractal dimension ($D_f$) of vorticity iso-surfaces and the local energy dissipation rate ($\epsilon$) in isotropic turbulent flows. The technical approach involves downloading DNS velocity field data from the Johns Hopkins Turbulence Database (JHTDB), computing velocity gradients via finite differences, extracting iso-surfaces, calculating $D_f$ using a box-counting algorithm, computing $\epsilon$, and performing statistical correlation analysis with block-bootstrapping confidence intervals and family-wise error correction. 

**Critical Data Note**: The implementation targets JHTDB as the primary source. If JHTDB data is unavailable or not in the "Verified Datasets" block, the system will fall back to a **Phase-Shifted DNS** generator (a verified null model derived from real DNS) for algorithm validation and robustness checks, but **not** for the primary hypothesis testing of Reynolds number scaling. The plan explicitly distinguishes between "Targeted Data" (JHTDB) and "Verified Fallbacks" (Phase-Shifted DNS).

## Technical Context

**Language/Version**: Python 3.10  
**Primary Dependencies**: `numpy`, `scipy`, `scikit-learn`, `pandas`, `requests`, `tqdm`, `h5py` (for HDF5 DNS data), `matplotlib`, `pytest`  
**Storage**: Local file system (GitHub Actions ephemeral storage), temporary `data/` directory for downloaded chunks  
**Testing**: `pytest` with unit tests for synthetic data (Menger sponge, Taylor-Green vortex, Phase-Shifted DNS)  
**Target Platform**: Linux (GitHub Actions standard runner)  
**Project Type**: Scientific computing library / CLI pipeline  
**Performance Goals**: Peak memory ≤ 6 GB, Total runtime ≤ 6 hours, Step runtime ≤ 30 minutes  
**Constraints**: No GPU, no deep learning, streaming/chunked processing for large-scale grids, strict adherence to constitution principles (Reproducibility, Data Hygiene).  
**Scale/Scope**: Processing of 3 Reynolds number datasets (Re_λ = 200, 400, 600) if available; otherwise, fallback to Re_λ = 200 with null-model validation.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Implementation Plan |
|-----------|--------|--------------------------------|
| **I. Reproducibility** | ✅ PASS | Plan mandates pinned `requirements.txt`, random seeds, and fetching data from canonical sources (JHTDB) *if available*. If JHTDB is unavailable, the plan switches to a **verified** Phase-Shifted DNS generator (with documented seed) to ensure reproducibility without fabricating URLs. |
| **II. Verified Accuracy** | ✅ PASS | Plan requires citations in `research.md` to be from the "Verified datasets" block. If JHTDB is not in the block, the plan does **not** invent a URL but uses a verified fallback or flags the gap. No external URLs are assumed verified. |
| **III. Data Hygiene** | ✅ PASS | Pipeline will checksum downloaded files and store derivations in new files under `data/`. No in-place modification. |
| **IV. Single Source of Truth** | ✅ PASS | Output schemas define exact fields for $D_f$, $\epsilon$, and correlation results, ensuring figures trace to `data/` rows. |
| **V. Versioning Discipline** | ✅ PASS | Artifacts will be versioned via content hashes in the state file (managed by the runtime). |
| **VI. Statistical Power** | ✅ PASS | Plan explicitly enforces $n \ge 1$ independent samples (via multi-snapshot pooling) and A sufficient number of bootstrap iterations (block-bootstrapping) as per spec US-3 and Constitution Section VI. |
| **VII. Computational Runtime** | ✅ PASS | Plan mandates chunked processing, CPU-only libraries, and job segmentation to meet ≤30 min/step and ≤6h total. |

## Project Structure

### Documentation (this feature)

```text
specs/001-fractal-dimension-turbulence/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-051-investigating-the-relationship-between-f/code/
├── __init__.py
├── main.py              # CLI entry point
├── config.py            # Configuration (Re_λ values, thresholds)
├── data/
│   ├── download.py      # JHTDB fetcher (with fallback logic)
│   └── preprocess.py    # Chunking and streaming logic
├── analysis/
│   ├── gradients.py     # Velocity gradient tensor (finite differences)
│   ├── fractal.py       # Box-counting algorithm
│   ├── dissipation.py   # Energy dissipation rate calculation
│   └── stats.py         # Correlation, block-bootstrap, FWE correction
├── validation/
│   ├── synthetic_menger.py      # Test for US-1
│   ├── synthetic_taylor_green.py # Test for US-2
│   └── null_model.py            # Phase-Shifted DNS generator
└── utils/
    └── logging.py       # Reproducible logging with seeds

tests/
├── contract/
│   └── test_schemas.py  # Validates output against contracts/*
├── integration/
│   └── test_pipeline.py # End-to-end synthetic test
└── unit/
    ├── test_fractal.py
    └── test_dissipation.py
```

**Structure Decision**: Single project structure selected to minimize overhead for a scientific pipeline. Modules are separated by domain (data, analysis, validation) to enforce modularity and testability.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Chunked Processing | A large three-dimensional float array is approximately several gigabytes in size..; full gradient + vorticity + epsilon maps exceed high RAM capacity

The research question remains: [Insert Research Question Here].
The method remains: [Insert Method Here].
References: [Insert References Here].. | Loading full 3D grids into memory at once would violate Constitution Section VII and US-5. |
| Block Bootstrapping | Required for robust CI estimation on spatially correlated turbulence data. | Standard i.i.d. bootstrapping would underestimate variance due to spatial autocorrelation. |
| Null Model (Phase-Shifted) | Required to decouple geometric thresholding from energetic magnitude (scientific soundness). | Simple synthetic generators (Gaussian) lack the necessary spectral properties for valid comparison. |
| Multi-Snapshot Pooling | Required to achieve n≥100 independent samples (Sufficient separation). | Single-snapshot sampling is physically impossible for the required independence. |

## Data Availability & Fallback Strategy

1. **Primary Target**: JHTDB (https://turbulence.pha.jhu.edu/). The pipeline attempts to download data for Re_λ = 200, 400, 600.
2. **Verification Check**: The pipeline checks if the JHTDB URL is in the "Verified Datasets" block.
   - **If Verified**: Proceed with real data.
   - **If Not Verified**: 
     - Log a **Critical Warning**: "JHTDB data not in verified block. Primary hypothesis testing (Re-scaling) cannot be performed with verified data."
     - Switch to **Phase-Shifted DNS** generator (derived from a verified local copy or verified HuggingFace mirror) for **algorithm validation** and **null model comparison** only.
     - Mark H3 (Re-scaling) as **Unverified** in final results.
3. **Contract Validation**: All output artifacts (CSV, JSON) are validated against `contracts/*.schema.yaml` before job completion.

## Contract Validation Step

The `main.py` pipeline includes a final step:
- Load `contracts/analysis_output.schema.yaml`.
- Validate `data/results/correlation_results.csv` against the schema.
- If validation fails, the job exits with error code 1.
- This ensures the "Plan ↔ contracts" consistency requirement is met.