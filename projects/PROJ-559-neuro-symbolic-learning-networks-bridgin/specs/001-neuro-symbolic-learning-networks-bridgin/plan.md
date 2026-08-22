# Implementation Plan: Neuro-Symbolic Learning Networks: Bridging Neural and Symbolic Reasoning in Education

**Branch**: `[PROJ-559-neuro-symbolic]` | **Date**: 2026-06-24 | **Spec**: `specs/PROJ-559-neuro-symbolic/spec.md`
**Input**: Feature specification from `/specs/PROJ-559-neuro-symbolic/spec.md`

## Summary

This project implements a comparative study framework to evaluate three explanation modalities (Neural-only, Symbolic-only, Neuro-Symbolic) for mathematics/logic problems. The system ingests problem data from public educational datasets (ASSISTments), generates distinct explanation artifacts using a lightweight LLM and a formal symbolic engine, and simulates student interactions via a calibrated Bayesian Knowledge Tracing (BKT) model. The pipeline culminates in a mixed-effects regression analysis comparing reasoning accuracy, response time, and self-reported comprehension across conditions, integrating both simulated and real student data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers` (CPU-optimized), `pandas`, `statsmodels`, `scipy`, `datasets` (Hugging Face), `pyyaml`, `psutil`, `ordinal` (for robustness check)  
**Storage**: Local filesystem (`data/raw`, `data/derived`, `data/pilot`), CSV/JSON artifacts  
**Testing**: `pytest` (unit/integration), `pytest-cov`  
**Target Platform**: Linux (GitHub Actions free-tier: 2 vCPU, 7GB RAM)  
**Project Type**: Research pipeline / Data analysis  
**Performance Goals**: 
- Inference latency < 2s per explanation on CPU (distilled model, see T013).
- Pipeline completion < 6 hours on free-tier runner.
- Memory usage < 7 GB peak.
**Constraints**: 
- No GPU access on primary runner (CPU-first design).
- Strict timeout handling for dataset downloads (300s limit, see T012).
- No external credentials for data access (open datasets only).
**Scale/Scope**: 
- ~ simulated interactions (a sufficient number of samples per condition, see T021).
- Real student records (integrated in final analysis, see T034a).
- A sufficient number of pilot records for BKT calibration will be used (see T030a).

> **Note on Compute Feasibility**: The plan adheres to the CPU-first constraint. The LLM component uses a quantized, distilled model (e.g., small-scale or smaller) running on CPU. If a specific model architecture proves computationally infeasible on CPU within the 6-hour window, the plan explicitly invokes a *manual* "GPU escape hatch" via a separate Kaggle kernel workflow (not automatic), but the primary design assumes CPU tractability via model quantization and dataset sampling.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence / Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **COMPLIANT** | `requirements.txt` pins all dependencies. Random seeds fixed in `code/` (see T002). External datasets fetched from canonical Hugging Face URLs (see T012). Pilot data generated via `code/pilot/synthetic_pilot_generator.py` (see T030a) to ensure reproducibility. Real data acquired via defined protocol (T034a). |
| **II. Verified Accuracy** | **COMPLIANT** | All dataset URLs cited from the "Verified datasets" block. Pilot data source is the generation script (T030a). Real data source is the defined protocol (T034a). |
| **III. Data Hygiene** | **COMPLIANT** | Raw data preserved in `data/raw/`. Checksums recorded in `state/` upon generation/acquisition (T030a, T034a). Derivations in `data/derived/`. No PII handling. |
| **IV. Single Source of Truth** | **COMPLIANT** | Analysis outputs (CSV) are the sole source for paper statistics. No hand-typed numbers. Output schema defined in `analysis_output.schema.yaml`. |
| **V. Versioning Discipline** | **COMPLIANT** | Artifacts tracked via content hash in `state/`. Pilot/Real data versioned upon generation/acquisition (T030a, T034a). |
| **VI. Educational Evaluation Rigor** | **COMPLIANT** | Mixed-effects regression with fixed effects (condition, prior knowledge, difficulty) and random intercepts (problem, student). Effect sizes (Cohen's d) with confidence intervals reported. Calibration validated on hold-out set (Phase 2.5). |
| **VII. Explanation Traceability** | **COMPLIANT** | All explanation artifacts stored in `data/derived/explanations/` with metadata linking to `problem_id`, `model_version`, and `condition` (see `explanation.schema.yaml`). |

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-559-neuro-symbolic/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    ├── problem.schema.yaml
    ├── explanation.schema.yaml
    ├── simulation_log.schema.yaml
    ├── pilot_data.schema.yaml
    └── analysis_output.schema.yaml
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── raw/             # Downloaded datasets (ASSISTments, etc.)
│   ├── pilot/           # Human pilot data for calibration
│   └── real/            # Real student data for final analysis
├── derived/             # Processed data, explanations, logs
│   ├── explanations/    # Neural, Symbolic, Neuro-Symbolic artifacts
│   └── logs/            # Simulation logs (CSV)
├── src/
│   ├── loaders/         # Dataset downloaders with timeout handling
│   ├── generators/      # Explanation generators (Neural, Symbolic, Hybrid)
│   ├── simulators/      # BKT-based student simulator
│   ├── calibrators/     # BKT calibration logic
│   └── analysis/        # Mixed-effects regression scripts
├── tests/
│   ├── unit/            # Unit tests for generators and simulators
│   └── integration/     # End-to-end pipeline tests
└── main.py              # Entry point for pipeline orchestration

requirements.txt
```

**Structure Decision**: Single project structure chosen for simplicity and tight coupling between data generation and analysis. The `code/` directory contains all logic, while `data/` is strictly for artifacts (raw and derived). This aligns with the "Single Source of Truth" principle, ensuring all results trace back to specific files in `data/`.

## Complexity Tracking

*No violations detected requiring justification.*

## Phased Implementation

### Phase 0: Setup & Configuration
- **T001**: Resource Monitor Setup (Install `psutil`, configure logging, produce `data/derived/resource_usage.json`).
- **T002**: Initialize Python 3.11 Project (Create `venv`, `requirements.txt` with pinned versions, set random seeds).
- **T003**: Define Project Configuration (Create `config/project_config.yaml` with paths, seeds, and thresholds).

### Phase 1: Data Acquisition & Validation
- **T012**: Fetch ASSISTments Dataset (Download from `assistments/[year]` with 300s timeout, log exact error message on failure, produce `data/raw/assistments.csv`, verify `difficulty` and `skill` fields).
- **T012b**: Implement Download Timeout (Implement the specific error message: "ERROR: Failed to download [dataset name] within 300 seconds – aborting pipeline.").
- **T012-Test**: Test Timeout Handling (Verify T012 error message and exit code).
- **T012-Check**: Validate Dataset Fields (Ensure `difficulty` and `skill` exist in downloaded data).
- **T030a**: Generate/Synthesize Human Pilot Data (Execute `code/pilot/synthetic_pilot_generator.py` to produce `data/pilot/raw_pilot_data.csv` with checksum, ensuring reproducibility).
- **T034a**: Acquire Real Student Data (Execute defined protocol to acquire `data/real/raw_real_data.csv`, checksum, validate schema).
- **T034a-Design**: Define Real Data Study Protocol (Document randomization procedure for real data collection).
- **T035**: Verify Pilot and Real Data Existence (Check that `data/pilot/raw_pilot_data.csv` and `data/real/raw_real_data.csv` exist before any downstream tasks.).

### Phase 2: Calibration & Validation
- **T031**: Run BKT Calibration (Calibrate BKT parameters using pilot data, learn condition-specific shifts).
- **T031b**: Check Pilot Data (Validate `data/pilot/raw_pilot_data.csv` against `pilot_data.schema.yaml`).
- **T032**: Validate Calibration Metrics (Check RMSE ≤ 0.15, t-test p ≥ 0.10, report results).
- **Phase 2.5**: Hold-out Validation (Reserve [deferred] of pilot data, validate simulator on hold-out set to ensure external validity).

### Phase 3: Explanation Generation
- **T013**: Generate Neural Explanations (Use distilled LLM, produce `explanation_neural.txt`).
- **T014**: Generate Symbolic Explanations (Use symbolic engine, produce `explanation_symbolic.txt`).
- **T015**: Generate Neuro-Symbolic Explanations (Combine LLM narrative with symbolic trace, produce `explanation_neuro_symbolic.txt`).
- **T016**: Track Generation Success (Monitor success rate, ensure ≥95%, produce `data/derived/generation_success.json`).
- **T017**: Validate Explanations (Check against `explanation.schema.yaml`).
- **T017b**: Generate Neuro-Symbolic Explanations (Implement the hybrid explanation generation logic combining LLM and symbolic trace.).

### Phase 4: Simulation & Logging
- **T021b**: Configure Simulation Sample Size (Set `config/simulation_config.yaml` to a sufficient number of students per condition to ensure statistical power and representativeness.).
- **T021a**: Dry Run Simulation (Run on small subset, produce `data/derived/dryrun_logs.csv`).
- **T023**: Validate RT Distribution (Check for >2 consecutive empty bins, produce `data/derived/rt_distribution_validation.json`, fail if invalid).
- **T021**: Run Full Simulation (Generate a large volume of interactions using calibrated BKT).
- **T022**: Log Interaction (Record `correct`, `rt_seconds` (0.1s), `comprehension_rating` (1-5), write to CSV).
- **T024**: Merge Simulation Logs (Aggregate all logs into `data/derived/simulated_logs.csv`).
- **T024b**: Validate RT Distribution (Implement the binning logic and validation of response time distribution.)
- **T020**: Explain API Interface (Define deterministic API call for explanation delivery).

### Phase 5: Analysis & Reporting
- **T034**: Merge Real Data (Merge real data with simulated logs, add `data_source` fixed effect).
- **T043**: Validate Dataset Size (Check ≥5,000 records).
- **T040**: Run Ordinal Mixed-Effects Model (Robustness check for Likert data).
- **T042**: Compute Effect Sizes and Validate CI Width (Calculate Cohen's d, check CI width ≤ 0.20).
- **T042a**: Compute Effect Sizes (Implement the calculation of Cohen's d with 95% confidence intervals.).
- **T043b**: Validate CI Width (Validate that the confidence interval width for the primary comparison is sufficiently narrow to ensure precise estimation.)
- **T044**: Generate Results Report (Produce `results/regression_summary.md`).
