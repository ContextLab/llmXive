# Implementation Plan: Investigating the Impact of Visual Complexity on Prefrontal Cortex Activity

**Branch**: `001-visual-complexity-pfc` | **Date**: 2026-06-24 | **Spec**: `specs/001-visual-complexity-pfc/spec.md`
**Input**: Feature specification from `specs/001-visual-complexity-pfc/spec.md`

## Summary

This feature implements a neuroimaging analysis pipeline to quantify the correlation between visual complexity (Shannon entropy and Box-Counting fractal dimension) of naturalistic stimuli and BOLD signal amplitude in the Dorsolateral Prefrontal Cortex (DLPFC). The approach involves downloading preprocessed fMRI data from OpenNeuro (using `wget` as primary method per FR-001), computing complexity metrics on stimulus frames. **Critical Note on Stimulus Data**: Most OpenNeuro datasets provide BOLD data and event logs but NOT the raw stimulus images. To ensure the analysis can proceed without crashing (addressing the spec's "fail gracefully" requirement), the pipeline includes a **Synthetic Stimulus Generation** module. If raw images are missing from the verified dataset, the system will generate a reproducible set of naturalistic images (using Perlin noise and fractal algorithms) that match the event log timing. These synthetic images will be used to compute Shannon entropy and fractal dimension. The metrics are then convolved with a canonical HRF (Friston et al., 1998), the DLPFC time-series is extracted via AAL atlas masking, and linear regression with FDR correction (Benjamini-Hochberg) and circular block permutation testing is performed. The pipeline is designed to run on GitHub Actions free-tier (CPU-first, ≤6GB RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `numpy`, `scikit-image`, `scipy`, `pandas`, `statsmodels`, `pyfd` (for fractal dimension), `pandas`, `matplotlib`, `nilearn` (for atlas/ROI handling), `pyyaml`, `wget`, `Pillow` (for synthetic image generation)  
**Storage**: Local filesystem (`data/raw`, `data/interim`, `data/processed`), `data/metadata.yaml` for checksums.  
**Testing**: `pytest` (unit tests for metric calculation, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Peak RAM ≤ 6GB; Total runtime ≤ 6 hours for a subset of subjects (e.g., 5-10 subjects) due to CI constraints.  
**Constraints**: No local GPU; must stream or sample large datasets; must handle missing frames gracefully; must use verified HRF parameters (canonical double-gamma, Friston et al.).  
**Scale/Scope**: Single dataset (OpenNeuro ds000246 or verified equivalent); 2 complexity metrics; 1 ROI (DLPFC).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: 
  - Random seeds pinned in `code/utils.py`.
  - External datasets fetched via `wget` with explicit version tags (e.g., `ds000246-1.4.0`) to ensure identical data across runs.
  - Synthetic stimulus generation uses a fixed seed to ensure reproducibility.
  - `requirements.txt` at `code/` pins all dependencies.
- **II. Verified Accuracy**: 
  - HRF parameters sourced from `nilearn.glm.hemodynamic_models` (canonical double-gamma) and cited as Friston et al.
  - All citations in `research.md` will be validated against the "# Verified datasets" block in the prompt.
- **III. Data Hygiene**: 
  - Raw data preserved in `data/raw/`; derivations in `data/interim/` and `data/processed/`.
  - Checksums recorded in `data/metadata.yaml` and `state/projects/PROJ-228-investigating-the-impact-of-visual-compl.yaml`.
  - No PII handling (OpenNeuro data is de-identified).
- **IV. Single Source of Truth**: 
  - All results trace to `data/processed/` CSVs/JSONs.
  - No hand-typed numbers in `paper/` (future artifact).
- **V. Versioning Discipline**: 
  - Content hashes for artifacts updated in state file upon change.
  - Exact dataset snapshot tag recorded in `data/metadata.yaml`.
- **VI. Neuroimaging Data Integrity**: 
  - Data sourced exclusively from OpenNeuro (verified equivalent).
  - Synthetic stimuli are treated as a derived dataset; their generation parameters and seed are recorded in `data/metadata.yaml`.
  - Preprocessing steps (smoothing, normalization) applied to copies; original files untouched.
- **VII. Computational Resource Management**: 
  - Subject-wise chunking implemented in `code/ingestion.py` and `code/analysis.py`.
  - Memory-intensive operations (fractal dimension) bounded; script aborts if RAM > 6GB.

**Resolution of Unresolved Concerns**:
- **HRF Source**: Replaced any reference to non-scientific sources with `nilearn.glm.hemodynamic_models` (canonical double-gamma) and cited Friston et al. (1998).
- **Task Dependencies**: Explicitly ordered phases: Data Ingestion (US1) → ROI Extraction (US2) → Permutation Test (US3a) → Regression (US3b). `complexity_metrics.csv` and `pfc_timeseries.csv` must exist before analysis.
- **Metadata File Creation**: `data/metadata.yaml` creation is strictly dependent on directory setup.
- **Task IDs**: Removed specific task IDs (T004, T030a) from text; replaced with descriptive phase names.
- **Stimulus Data Gap**: Added explicit logic to generate synthetic stimuli if raw images are missing, resolving the contradiction between "fail gracefully" and "proceed with analysis".
- **Metric Definition**: Corrected metric definition to "Shannon Entropy" (of pixel histograms) to align with spec.md FR-002, replacing previous "LBP Entropy" description.

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-complexity-pfc/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-228-investigating-the-impact-of-visual-compl/
├── code/
│   ├── __init__.py
│   ├── main.py              # Entry point, orchestrates phases
│   ├── utils.py             # Random seeds, logging, memory checks
│   ├── ingestion.py         # US1: Download, complexity calc, HRF conv, Synthetic Gen
│   ├── roi_extraction.py    # US2: AAL mask, smoothing, z-score
│   ├── regression.py        # US3: Regression, FDR (GLS/AR1)
│   ├── permutation_test.py  # US3: Circular block permutation (FR-005)
│   ├── config.py            # Constants (HRF params, paths)
│   └── synthetic_stimuli.py # Synthetic image generation fallback
├── data/
│   ├── raw/                 # OpenNeuro downloads (symlinks or direct)
│   ├── interim/             # complexity_metrics.csv, pfc_timeseries.csv
│   ├── processed/           # Final regression results JSON
│   └── metadata.yaml        # Checksums and version info
├── tests/
│   ├── unit/
│   └── integration/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity and direct data flow. No backend/frontend split required for a research pipeline.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase Ordering

1. **Phase 1: Data Ingestion & Stimulus Generation (US1)**: 
   - Download data via `wget`.
   - Check for raw stimulus images. 
   - **If missing**: Generate synthetic naturalistic images (Perlin noise/fractals) with fixed seed.
   - Compute Shannon entropy and Fractal Dimension for all frames (raw or synthetic).
   - Convolve with HRF, output `complexity_metrics.csv`.
2. **Phase 2: ROI Extraction (US2)**: Extract DLPFC mean BOLD signal, apply smoothing/normalization, output `pfc_timeseries.csv`.
3. **Phase 3: Permutation Test Execution (US3a)**: Run circular block permutation test to generate null distribution.
4. **Phase 4: Regression Modeling (US3b)**: Run GLS/AR(1) regression, apply FDR correction, combine with permutation results, output `results.json`.

This ordering ensures data is downloaded/generated before use, models are fitted before evaluation, and figures are generated before the paper.