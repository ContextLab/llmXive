# Implementation Plan: The Cognitive Mechanisms Underlying Intuitive Moral Judgments in Virtual Environments

**Branch**: `134-cognitive-mechanisms-vr-judgments` | **Date**: 2026-06-26 | **Spec**: [link]
**Input**: Feature specification from `specs/134-the-cognitive-mechanisms-underlying-intu/spec.md`

## Summary
This plan implements a Bayesian hierarchical modeling pipeline to investigate how perceptual salience in VR environments influences intuitive moral judgments. The system ingests **real** Moral Foundations Questionnaire (MFQ) data from the verified OSF repository and **simulates** VR interaction logs based on Unity blend-shape parameters. This hybrid approach ensures the psychometric data is authentic while allowing controlled manipulation of the VR salience variable. The pipeline validates schemas against strict Pydantic models, estimates posterior distributions using PyMC5, and performs rigorous model comparison (WAIC/AIC) and sensitivity analysis. The system supports "Real Data Mode" (fetching OSF MFQ + generating VR logs) and "Simulation Mode" (fully synthetic) while strictly adhering to the "fail loudly" constraint for missing data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyMC5 (for Bayesian inference), PyTensor (backend), pandas, polars (for data manipulation), datasets (HuggingFace), pydantic (schema validation), numpy, scipy (statistical baselines), scikit-learn (preprocessing).  
**Storage**: Local `data/` directory (raw, processed, checksummed), HuggingFace Datasets cache.  
**Testing**: `pytest` (unit tests for schema validation, integration tests for pipeline steps).  
**Target Platform**: Linux (GitHub Actions runner: multiple CPU cores, several GB RAM) with automatic offload to Kaggle GPU for PyMC5 sampling if CUDA is detected and CPU fails.  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete end-to-end run (data fetch -> model fit -> PPC) within 6 hours on CPU (sampled data) or 9 hours on Kaggle GPU (full data).  
**Constraints**: 
- Must run on free-tier GitHub Actions (CPU-first). 
- No silent fallbacks to synthetic data if real data is missing (FR-006). 
- All random seeds pinned (NFR-001). 
- PyMC5 is mandated over PyMC3 (FR-002). **See Spec Deviation Log in `spec.md` for justification.**  
**Scale/Scope**: Single study analysis; dataset size variable (streaming supported for >7GB).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Detail |
|-----------|--------|-----------------------|
| **I. Reproducibility** | **Pass** | `requirements.txt` pins all deps; `random_seed` config in `config.yaml`; artifacts checksummed in `state/`. |
| **II. Verified Accuracy** | **Pass** | Citations in `research.md` restricted to the "Verified datasets" block; **Reference-Validator Agent runs on `research.md` before proceeding** (Constitution Principle II). |
| **III. Data Hygiene** | **Pass** | Raw data immutable; derivations in `data/processed/` with new filenames; PII scan in CI. |
| **IV. Single Source of Truth** | **Pass** | All stats in paper trace to `data/processed/` via `code/analysis/` scripts; no hand-typed numbers. |
| **V. Versioning Discipline** | **Pass** | Content hashes tracked in `state/PROJ-134-...yaml`; **`updated_at` timestamps updated on every artifact change** (Constitution Principle V). |
| **VI. VR Manipulation Fidelity** | **Pass** | Unity blend-shape parameters logged explicitly in `data/raw/vr_config.json`; simulation logic maps these to salience. |
| **VII. Psychometric Instrument Integrity** | **Pass** | MFQ validation logic checks against standard psychometric norms before analysis; VR adaptation checks included. |

## Project Structure

### Documentation (this feature)
```text
specs/134-the-cognitive-mechanisms-underlying-intu/
├── plan.md              # This file (Phase 2 output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (Existing artifacts referenced here)
│   ├── mfq.schema.yaml
│   ├── vr_log.schema.yaml
│   └── model_output.schema.yaml
├── spec_amendment_FR006.md # T090: Spec Amendment Document
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)
```text
code/
├── config.yaml          # Seeds, paths, mode (real/sim)
├── requirements.txt     # Pinned dependencies (PyMC5, etc.)
├── fetch_real_data.py   # FR-006: Real data ingestion & validation (OSF MFQ)
├── fetch_real_vr.py     # T092: VR data ingestion (if available, else fail)
├── simulate_vr.py       # FR-003: VR log simulation with blend-shapes (T014)
├── preprocessing.py     # Data cleaning, merging, streaming logic
├── models/
│   ├── __init__.py
│   ├── bayesian_model.py # FR-002: PyMC5 hierarchical model
│   └── baseline_model.py # Frequentist baseline for comparison
├── analysis/
│   ├── sensitivity.py    # FR-005: Sensitivity analysis
│   ├── comparison.py     # FR-004: AIC/WAIC & PPC
│   └── bonferroni.py     # US3: Bonferroni correction implementation
└── utils/
    ├── schema.py         # Pydantic models for validation
    └── checksum.py       # Data hygiene utilities

data/
├── raw/                  # Downloaded raw files (checksummed)
│   ├── osf_mfq.parquet   # Real MFQ data
│   └── vr_config.json    # Unity config
├── processed/            # Cleaned, merged datasets
│   └── synthetic_logs.csv # T014: Generated synthetic logs
└── logs/                 # Execution logs, seed records

tests/
├── unit/
│   └── test_schemas.py
└── integration/
    └── test_pipeline.py
```

**Structure Decision**: Single project structure selected to maintain tight coupling between data ingestion, simulation, and modeling logic, ensuring reproducibility and minimizing data transfer overhead on the CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **PyMC5 over PyMC3** | Spec explicitly mandates PyMC5 (FR-002) per **Deviation Log in `spec.md`** for modern inference backends. | PyMC3 is deprecated and incompatible with current PyTensor versions; using it would violate the spec. |
| **GPU Escape Hatch** | Bayesian hierarchical models with large datasets may exceed 6h on CPU. | A pure CPU approximation (e.g., variational inference with low precision) would violate statistical rigor; the plan uses a real scaled GPU run via Kaggle auto-offload. |
| **Strict "Fail Loudly"** | FR-006 requires no synthetic fallback for real data. | A silent fallback would mask data availability issues, violating the "Verified Accuracy" constitution principle. |
| **T095 Logic** | T095 depends on T090's output. | T095 will check for `spec_amendment_FR006.md` and validate the presence of "APPROVED" string before allowing simulation. |
