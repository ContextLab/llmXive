# Implementation Plan: llmXive follow-up: extending "OmniOpt: Taxonomy, Geometry, and Benchmarking of Modern Optimizers"

**Branch**: `001-spectral-optimizer-prediction` | **Date**: 2026-09-06 | **Spec**: `specs/001-spectral-optimizer-prediction/spec.md`
**Input**: Feature specification from `specs/001-spectral-optimizer-prediction/spec.md`

## Summary

This feature implements a pipeline to extract spectral signatures (Condition Number, Spectral Entropy) from initial gradient covariance matrices of small-scale models and test for a statistically significant **association** between these signatures and the rank-ordered performance of optimizer families (e.g., Adam, SGD, Lion) as defined by the OmniOpt benchmark. The approach validates the hypothesis that "pre-flight" spectral diagnostics correlate with optimizer suitability without full training. The pipeline runs on a CPU-first GitHub Actions runner, utilizing streaming for dataset access, aggressive memory management, and a two-tier ground truth protocol (Paper Tables primary, Re-run secondary) to fit within 6-hour runtime and ~7GB RAM constraints.

**Note on Spec Inconsistency**: The `spec.md` requires "tail decay exponent" (power-law MLE). This plan replaces it with "Spectral Entropy" due to statistical unsoundness of MLE on N=50. The `spec.md` must be updated to remove the "tail decay" requirement (Flagged for Kickback).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch`, `transformers`, `scikit-learn`, `datasets`, `numpy`, `scipy`, `pandas`, `pyyaml`  
**Storage**: Local temporary files in `data/` (checksummed), JSON/CSV artifacts for spectral features and labels.  
**Testing**: `pytest` (unit tests for spectral extraction, integration tests for pipeline flow, mock tests for OmniOpt lookup).  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7GB RAM).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: < 6 hours total runtime; < 7GB peak RAM; < 15 mins per eigenvalue decomposition task.  
**Constraints**: CPU-only execution for spectral extraction; no local GPU; strict adherence to multi-step proxy training; strict handling of singular matrices; no fabrication of OmniOpt data.  
**Scale/Scope**: diverse model architectures (N < 20 if data source is limited); + optimizer families; TinyImageNet/C4 subsets.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: All random seeds will be pinned in `code/`. External datasets (TinyImageNet) fetched via canonical Hugging Face URLs. OmniOpt labels derived from a static, versioned lookup table (Paper Tables) or re-run sub-experiments via `re_run_omniopt_subexperiment.py` as a secondary verification.
- **Principle II (Verified Accuracy)**: Citations for TinyImageNet will use the verified Hugging Face URLs. OmniOpt benchmark claims will reference the specific "OmniOpt" paper or dataset source. **The Reference-Validator Agent will be executed** on all citations before artifact write.
- **Principle III (Data Hygiene)**: Raw dataset shards downloaded to `data/raw/` with checksums. Derived spectral features written to `data/processed/` as new files. No in-place modification.
- **Principle IV (Single Source of Truth)**: Final correlation coefficients and p-values in `paper/` will be generated programmatically from `data/processed/results.json`.
- **Principle V (Versioning)**: All artifacts under `data/` and `code/` will carry content hashes in `state/`. **The pipeline will explicitly update the `updated_at` timestamp** in `state/projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo.yaml` upon any artifact change.
- **Principle VI (Spectral Analysis Fidelity)**: Extraction strictly limited to an initial phase of steps on specified proxy datasets (TinyImageNet/C4) and model architectures. Deviation triggers failure.
- **Principle VII (Ground Truth Alignment)**: "Optimal mechanism family" labels strictly mapped from the OmniOpt benchmark results (Paper Tables primary, Re-run secondary). No heuristic approximations.

## Project Structure

### Documentation (this feature)

```text
specs/001-spectral-optimizer-prediction/
├── plan.md              # This file (Phase 0 output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (Deliverable of Phase 2)
```

### Source Code (repository root)

```text
projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── spectral_extractor.py      # Implements US-1: Gradient covariance & feature extraction (Spectral Entropy, Cond Num)
│   ├── label_mapper.py            # Implements US-2: OmniOpt lookup & labeling
│   ├── re_run_omniopt_subexperiment.py # Implements US-2 Fallback: Re-run specific benchmark if label missing
│   ├── correlation_analyzer.py    # Implements US-3: Spearman correlation & significance testing
│   ├── utils/
│   │   ├── seeds.py               # Seed pinning
│   │   ├── logging.py             # Structured logging
│   │   └── memory_monitor.py      # RAM usage tracking
│   └── main_pipeline.py           # Orchestrator
├── data/
│   ├── raw/                       # Downloaded dataset shards (checksummed)
│   ├── processed/
│   │   ├── spectral_features.csv  # Extracted features
│   │   ├── labeled_dataset.json   # Features + Labels
│   │   └── results.json           # Correlation metrics & p-values
│   └── omniopt_lookup.json        # Static ground truth mapping (Primary: Paper Tables)
├── tests/
│   ├── unit/
│   │   ├── test_spectral_extractor.py
│   │   └── test_label_mapper.py
│   └── integration/
│       └── test_full_pipeline.py
└── state/
    └── projects/PROJ-1010-llmxive-follow-up-extending-omniopt-taxo.yaml
```

**Structure Decision**: Single project structure chosen to maintain tight coupling between extraction, labeling, and analysis phases, facilitating end-to-end reproducibility and memory monitoring within a single runner session.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Spearman Correlation | Classification (LogReg/RF) is statistically invalid for N=20. | Classification would result in overfitting and meaningless accuracy metrics. |
| Spectral Entropy | Power-law MLE on a limited set of eigenvalues is statistically unsound (high variance). | Power-law fit on a small sample size is noise; Entropy is robust and well-defined. |
| Two-Tier Ground Truth | No verified URL for OmniOpt data in the wild. | Static JSON alone violates reproducibility; re-run ensures canonical ground truth if primary source is missing. |
| Aggressive Memory Management | Medium-scale param models + a moderate number of steps + full covariance exceeds 7GB RAM. | Storing full gradients or using large batches would crash the runner. |

**Note**: The `spec.md` requirement for "tail decay exponent" is a blocking inconsistency. This plan uses "Spectral Entropy" and flags the spec for update.