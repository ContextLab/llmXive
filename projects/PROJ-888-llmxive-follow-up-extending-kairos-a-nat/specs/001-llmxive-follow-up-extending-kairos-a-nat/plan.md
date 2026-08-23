# Implementation Plan: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Branch**: `001-llmxive-kairos-discrete-scaling` | **Date**: 2026-08-24 | **Spec**: `specs/001-llmxive-follow-up-extending-kairos-a-nat/spec.md`

## Summary

This project investigates how the minimum information density required for stable long-horizon forecasting in embodied agents scales as input modality shifts from continuous visual streams to sparse, discrete sensor streams. We will implement a reproducible pipeline to convert the `lerobot/libero_plus` dataset into discrete state vectors with configurable quantization (4, 6, 8, 16-bit), inject telemetry noise, and evaluate a CPU-only Kairos Hybrid Linear Temporal Attention model. The study will determine the stability threshold where the Total Mean Squared Error (MSE) of the discrete modality significantly exceeds the continuous baseline using Linear Mixed-Effects Models (LMM) and power analysis, strictly adhering to GitHub Actions Free Tier constraints (limited compute resources, 7GB RAM, 6h runtime).

**Critical Methodological Adjustment**: To ensure scientific validity and CPU feasibility, the "Fair Baseline" will be a **frozen pre-trained continuous model** evaluated on **quantized ground truth** (derived from continuous data). The "Discrete" arm will fine-tune only the projection layer. This isolates the modality shift effect from training convergence artifacts and ensures the CPU budget is sufficient.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `datasets` (Hugging Face), `pandas`, `statsmodels` (for LMM), `scikit-learn`, `numpy`, `psutil`, `pyyaml`, `pytest`, `simr` (for power analysis simulation)  
**Storage**: Local file system (`data/`, `code/`, `results/`); Parquet source, JSON-serialized discrete outputs.  
**Testing**: `pytest` (unit tests for quantization logic, integration tests for pipeline), `contract` tests for schema validation.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 vCPU, ~7GB RAM).  
**Project Type**: Research pipeline / Data processing & Statistical Analysis.  
**Performance Goals**: 
- Data conversion: ≤ 30 mins for full subset.
- Training (Fine-tuning): ≤ 4 hours (graceful exit at 6h).
- RAM: Peak < 7GB.
**Constraints**: 
- NO GPU, NO CUDA, NO `bitsandbytes`.
- Velocities derived from *continuous* data before quantization.
- Noise added to continuous data before quantization.
- 1-bit degeneracy detection (exit code 1).
**Scale/Scope**: 
- Dataset: `lerobot/libero_plus` (subset sampled to fit RAM/time).
- Horizons:, 500, 1000 steps.
- Quantization:, 6, 8, 16-bit.
- Factorial Design: 2x2 (Continuous/Discrete) x (Noise/NoNoise).

## Constitution Check

*GATE: Must pass before Phase 0 research. Note: Principle VII requires amendment.*

| Principle | Compliance Status | Evidence/Action |
|-----------|-------------------|-----------------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned `requirements.txt`, fixed random seeds, and automated download of `lerobot/libero_plus` via `datasets` library. |
| **II. Verified Accuracy** | **PASS** | All citations (Kairos paper, LMM methodology) will be validated by Reference-Validator. No fabricated URLs; dataset source verified. |
| **III. Data Hygiene** | **PASS** | Pipeline creates new derived files (`data/discrete_4bit.json`, etc.) without modifying raw parquet. Checksums recorded in `state/`. |
| **IV. Single Source of Truth** | **PASS** | `results/stats_results.json` and `results/power_analysis_report.json` are the sole sources for paper figures. |
| **V. Versioning Discipline** | **PASS** | Artifacts in `data/` and `results/` will be hashed; `state/` updated on change. |
| **VI. Resource-Constrained Stability** | **PASS** | Plan explicitly targets CPU-only execution; metrics `peak_ram_gb` and `total_time_h` are logged and validated against 7GB/6h limits. |
| **VII. Discrete Modality Error** | **FAIL (Amendment Required)** | Constitution mandates t-test/Wilcoxon; Plan uses LMM for autocorrelation. **Action**: Flagged for amendment. Plan implements LMM. Also, MSE is now explicitly normalized by state space dimensionality (`MSE / D`) to satisfy the calculation method. Cumulative error growth rate is explicitly tracked. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-kairos-discrete-scaling/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── prediction.schema.yaml
│   └── result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py          # HF dataset loading + Schema Verification
│   │   ├── quantizer.py       # Pre-quantization derivation & noise injection
│   │   └── validator.py       # 1-bit collapse detection
│   ├── model/
│   │   ├── __init__.py
│   │   ├── kairos_adapter.py  # Heuristic initialization logic
│   │   └── training_loop.py   # CPU-only fine-tuning & inference
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── metrics.py         # MSE (normalized), cumulative error rate
│   │   └── stats.py           # LMM, Power Analysis (LMM simulation), Bootstrap
│   └── main.py                # Orchestration script
├── tests/
│   ├── __init__.py
│   ├── contract/              # Schema validation tests
│   ├── unit/                  # Quantization logic, noise injection, 1-bit collapse
│   └── integration/           # End-to-end pipeline (subset)
├── data/
│   ├── raw/                   # Downloaded parquet (if cached)
│   ├── processed/             # Discrete JSON outputs
│   └── checksums.yaml         # Artifact hashes
├── results/
│   ├── stats_results.json
│   ├── power_analysis_report.json
│   └── resource_profile.json
├── state/
│   └── projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat.yaml
├── docs/
│   └── README.md
└── requirements.txt
```

**Structure Decision**: Single `code/` directory with modular sub-packages (`data`, `model`, `analysis`) to enforce separation of concerns between data transformation, model logic, and statistical analysis. This aligns with the requirement for reproducible, isolated runs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **LMM vs. T-test** | Time-series errors are autocorrelated; paired t-tests assume independence. | Standard t-test would yield inflated Type I error rates, violating scientific rigor (Constitution VII). **Requires Amendment**. |
| **Pre-quantization Derivation** | Deriving velocity from quantized data amplifies noise artifacts. | Post-quantization derivation would confound "modality shift" with "quantization noise," invalidating the core hypothesis. |
| **Heuristic Initialization** | Random initialization on discrete data may prevent convergence within 6h. | Random init risks non-convergence; heuristic init (matching continuous stats) isolates the modality shift variable. |
| **Frozen Baseline** | Training a full continuous model on CPU may fail to converge in 4h. | A frozen pre-trained baseline ensures the comparison is valid and not confounded by optimization failure. |

## Phases & Tasks

### Phase 0: Data Verification & Preparation
- **T001**: Verify `lerobot/libero_plus` availability via `datasets.load_dataset`. **Fail-Hard** if schema missing `observations.ee_pos` or `observations.positions`.
- **T002**: Generate 2x2 factorial datasets: (Continuous+NoNoise), (Continuous+Noise), (Discrete+NoNoise), (Discrete+Noise).
- **T003**: Implement 1-bit collapse detection (exit code 1) in `data/validator.py`.

### Phase 0.5: Power Analysis
- **T004**: Perform LMM-based power simulation (using `simr` logic) to determine N for Cohen's d=0.8, Power=0.8. Output `power_analysis_report.json`.

### Phase 1: Model Execution
- **T005**: Load frozen pre-trained Kairos weights.
- **T006**: Fine-tune discrete projection layer on quantized data.
- **T007**: Evaluate both arms on quantized ground truth.

### Phase 2: Analysis
- **T008**: Compute Total MSE (normalized by D), cumulative error rate.
- **T009**: Run LMM with `episode_id` as random effect.
- **T010**: Identify stability threshold (CI upper bound > 1.0).

## Risk Management

- **Risk**: `lerobot/libero_plus` not available. **Mitigation**: Fail-Hard with clear error; no synthetic substitution.
- **Risk**: CPU training time exceeds 6h. **Mitigation**: Use frozen baseline; fine-tune only projection layer; sample episodes.
- **Risk**: 1-bit collapse. **Mitigation**: Detect and exit with code 1.