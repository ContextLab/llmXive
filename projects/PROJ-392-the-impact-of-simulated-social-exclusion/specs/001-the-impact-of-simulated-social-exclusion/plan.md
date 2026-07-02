# Implementation Plan: 001-social-exclusion-reward-neural

**Branch**: `001-social-exclusion-reward-neural` | **Date**: 2024-01-15 | **Spec**: `specs/001-social-exclusion-reward-neural/spec.md`
**Input**: Feature specification from `specs/001-social-exclusion-reward-neural/spec.md`

## Summary

This feature implements a CPU-tractable fMRI analysis pipeline to investigate the association between simulated social exclusion (Cyberball paradigm) and subsequent neural responses to reward (ventral striatum, OFC). The system downloads BIDS-formatted datasets (OpenNeuro), preprocesses them using CPU-optimized methods (Nilearn/AFNI), extracts ROI beta estimates for specific contrasts, performs second-level mixed-effects modeling with FWE correction, and generates sensitivity analyses and visualizations. 

**Critical Feasibility Note**: The original spec assumed a single dataset containing both Cyberball and a subsequent reward task (e.g., MID). No such dataset exists in OpenNeuro (The dataset is Cyberball only.; The dataset is Cyberball only; The dataset is MID only.). To proceed, this plan adopts a **Feasibility Pivot**: 
1. **Primary Path**: Analyze the neural correlates of the *exclusion task itself* (e.g., anticipation of social feedback) if the dataset contains such a component.
2. **Secondary Path (Simulation)**: If the dataset lacks a reward task, the pipeline will generate **synthetic reward task data** (simulated BOLD responses) to demonstrate the analysis pipeline, clearly labeling these as simulations.
3. **Alternative Path**: If a combined dataset is found later, the pipeline will switch to the interaction contrast.

All processing is constrained to run on GitHub Actions free-tier runners (vCPU, 7 GB RAM) without GPU acceleration.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `nibabel`, `nilearn` (v0.10+), `scikit-learn`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `scipy`, `openneuro-py`.  
**Storage**: Local filesystem (`data/raw-fmri/`, `data/processed-fmri/`, `data/behavioral/`). No external database.  
**Testing**: `pytest` (contract tests against YAML schemas, unit tests for statistical logic).  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Computational research pipeline (CLI).  
**Performance Goals**: Preprocessing ≤4 hours for N=10-15 (downsampled) on CPU-only runner; Total runtime ≤6 hours; Memory ≤7 GB.  
**Constraints**: No GPU/CUDA; No large LLM inference; Chunked processing for memory management; Strict BIDS compliance; **Downsampling to 4mm** if memory >6GB.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/`. External datasets fetched via deterministic OpenNeuro CLI (`openneuro-py`). `requirements.txt` pins versions. |
| **II. Verified Accuracy** | **PASS** | Citations in `research.md` will be validated against the "Verified datasets" block. No invented URLs. |
| **III. Data Hygiene** | **PASS** | Raw data stored in `data/raw-fmri/` with checksums. Derived data in `data/processed-fmri/`. No in-place modifications. PII scan via `Repository-Hygiene Agent`. |
| **IV. Single Source of Truth** | **PASS** | All figures/stats in `paper/` trace to `data/` rows and `code/` blocks. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for artifacts. `state/` updated on artifact changes. |
| **VI. Neuroimaging Data Integrity** | **PASS** | Raw scans preserved in `data/raw-fmri/`. Preprocessing scripts in `code/preprocess/` produce `data/processed-fmri/`. Provenance files record pipeline versions. |
| **VII. Behavioral Manipulation Standardization** | **PASS** | **Replication Strategy**: A deterministic script `code/manipulation/cyberball.py` is generated to **replicate** the original paradigm parameters for documentation and transparency. It does not generate the data but verifies the original study's timing if metadata is available. Behavioral data is extracted from BIDS `participants.tsv` or `task-*.tsv`, checksummed, and stored in `data/behavioral/`. If missing, the system flags the group label as a 'proxy variable'. |

## Project Structure

### Documentation (this feature)

```text
specs/001-social-exclusion-reward-neural/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-392-the-impact-of-simulated-social-exclusion/
├── code/
│   ├── __init__.py
│   ├── main.py              # Entry point for pipeline execution
│   ├── download.py          # Dataset acquisition (OpenNeuro via openneuro-py)
│   ├── preprocess.py        # CPU-tractable preprocessing (Nilearn/AFNI)
│   ├── roi_extraction.py    # Beta extraction from AAL/Harvard-Oxford
│   ├── analysis.py          # Second-level mixed-effects, FWE correction, sensitivity
│   ├── viz.py               # Plotting (bar plots, SPM overlays)
│   ├── manipulation/        # Replication scripts for documentation
│   │   └── cyberball.py     # Replicates original paradigm parameters
│   └── utils.py             # Logging, checksumming, BIDS helpers
├── data/
│   ├── raw-fmri/            # Downloaded raw BIDS data
│   ├── processed-fmri/      # Preprocessed NIfTI + GLM estimates
│   ├── behavioral/          # Condition labels, distress scores (checksummed)
│   └── synthetic/           # (Optional) Synthetic reward task data if needed
├── tests/
│   ├── contract/            # Schema validation tests
│   ├── integration/         # Full pipeline tests (sample data)
│   └── unit/                # Statistical logic tests
├── docs/
│   └── paper/               # Generated reports and visualizations
└── requirements.txt
```

**Structure Decision**: Single project structure (Option 1) selected. The pipeline is linear (Download -> Preprocess -> Analyze -> Visualize) and does not require separate frontend/backend services. All logic resides in `code/` for reproducibility and version control. `data/behavioral/` is explicitly included.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Chunked Processing** | fMRIPrep/Nipype can exceed 7 GB RAM on full datasets. | Processing all participants at once risks OOM crashes on GitHub Actions free tier. |
| **Downsampling** | High resolution may exceed 7GB RAM on 2 vCPU. | Full 3mm processing is infeasible; A minimum threshold is established for ROI analysis.. |
| **Sensitivity Analysis Loop** | Must test multiple threshold combinations (smoothing × 3 ROI radii). | Single-run analysis fails SC-003 (robustness check) and risks methodological rejection. |
| **CPU-Only Constraints** | No GPU available on free tier. | GPU-dependent libraries (e.g., `torch` with CUDA) would prevent execution; CPU-tractable alternatives (Nilearn/AFNI) are required. |
| **Feasibility Pivot** | No single dataset contains both Cyberball and Reward tasks. | The original design is impossible; the plan must pivot to simulation or single-task analysis. |


## Implementation Phases

### Phase 0: Data Acquisition & Feasibility Check
- **Task 0.1**: Download raw BIDS dataset (ds000246) via `openneuro-py`.
- **Task 0.2**: Verify dataset contents (Cyberball task only? Missing reward task?).
- **Task 0.3**: If reward task is missing, generate **synthetic reward task data** (simulated BOLD) or flag as **blocking issue** and halt.
- **Task 0.4**: Checksum raw data and record in `data/raw-fmri/`.

### Phase 0.5: Design Verification
- **Task 0.5**: Inspect BIDS task files to determine if the design is **within-subject** (each participant does both exclusion and inclusion) or **between-subject**.
- **Task 0.6**: Select statistical model: Mixed-effects (within-subject) or Independent t-test (between-subject).

### Phase 1: Preprocessing (CPU-Optimized)
- **Task 1.1**: Slice timing correction.
- **Task 1.2**: Realignment (motion correction).
- **Task 1.3**: Normalization to MNI space (using `nilearn.image.resample_img` with **4mm** isotropic resolution if memory >6GB).
- **Task 1.4**: Smoothing: 6mm FWHM (primary), with sensitivity analysis at 4mm and 8mm.
- **Task 1.5**: **Memory Management**: Process participants in manageable batches.. Monitor RAM; if >6GB, downsample to 4mm.
- **Task 1.6**: Log **Preprocessing Completion Rate** (Success/Total) for SC-004.

### Phase 2: ROI Definition & Extraction
- **Task 2.1**: Define ROIs: Ventral Striatum (AAL), OFC (Harvard-Oxford).
- **Task 2.2**: Extract beta estimates for 'Reward > Neutral' (receipt) and 'Anticipation > Baseline' (anticipation).
- **Task 2.3**: Store in `data/extracted/` (CSV/Parquet).

### Phase 2.5: Behavioral Validation (FR-011)
- **Task 2.5.1**: Extract distress scores or condition labels from `data/behavioral/`.
- **Task 2.5.2**: If behavioral data exists, validate the manipulation (e.g., distress > threshold).
- **Task 2.5.3**: If missing, flag group label as 'proxy variable' and log limitation.

### Phase 3: Statistical Analysis
- **Task 3.1**: Compute the interaction contrast: (Exclusion_Reward - Exclusion_Neutral) - (Inclusion_Reward - Inclusion_Neutral).
- **Task 3.2**: Perform second-level mixed-effects model (or paired t-test) with FWE correction (SVC).
- **Task 3.3**: Calculate Cohen's d and 95% CI.

### Phase 4: Sensitivity Analysis
- **Task 4.1**: Sweep smoothing (multiple kernel widths) × ROI radius (8, 10, 12 mm).
- **Task 4.2**: Calculate **Effect Size Stability** (Cohen's d within 20% of primary) and **Direction Stability**.
- **Task 4.3**: Report consistency rate (≥6/9 combinations).

### Phase 5: Visualization & Reporting
- **Task 5.1**: Generate bar plots (mean ± SEM) with p-value annotations.
- **Task 5.2**: Generate SPM overlays on MNI template.
- **Task 5.3**: Compile summary report.
- **Task 5.4**: **Framing Accuracy Check** (SC-005): Scan report for causal verbs; ensure associational language.
- **Task 5.5**: **Future Recommendations** (FR-010): Generate text recommending ≥30 participants per group.

## Constitution Check (Detailed)

- **Principle VII**: The script `code/manipulation/cyberball.py` is a **replication** of the original paradigm for transparency. It does not generate the data but documents the timing parameters. Behavioral data is extracted from BIDS, checksummed, and stored in `data/behavioral/`.
