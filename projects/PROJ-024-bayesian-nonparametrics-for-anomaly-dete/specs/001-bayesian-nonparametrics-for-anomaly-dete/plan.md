# Implementation Plan: Bayesian Nonparametrics for Anomaly Detection in Time Series

**Branch**: `feature/bayesian-anomaly-detection` | **Date**: 2026-06-12 | **Spec**: [link to spec.md]  
**Input**: Feature specification from `/specs/001-bayesian-nonparametrics-for-anomaly-dete/spec.md`

## Summary
Implement a streaming anomaly detection service based on Dirichlet Process Gaussian Mixture Models (DP‑GMM). The system will ingest univariate time‑series observations, maintain a posterior over mixture components, and output calibrated anomaly scores with uncertainty estimates. A complementary threshold calibrator will adapt decision boundaries from score distributions. All artifacts will obey the project constitution (reproducibility, data hygiene, numerical stability, etc.).

**Note on Streaming**: "Streaming" refers to mini-batch updates on sliding windows (not true online ADVI). The `StreamingDPGMM` service wrapper maintains window state and performs incremental posterior updates at periodic intervals on a specified observation window.

## Technical Context
- **Language/Version**: Python 3.11
- **Primary Dependencies**:  
  - `numpy==1.26.*`  
  - `pandas==2.2.*`  
  - `scipy==1.13.*`  
  - `torch==2.3.*` (for Pyro)  
  - `pyro-ppl==1.9.*` (ADVI inference)  
  - `scikit-learn==1.5.*` (baseline models)  
  - `pyyaml==6.0.*` (config handling)  
  - `pytest==8.2.*` (testing)  
  - `jsonschema==4.22.*` (contract validation)  
- **Storage**: File‑based CSVs under `data/raw/`; processed artefacts under `data/processed/`; model checkpoints under `state/projects/`.
- **Testing**: `pytest` with `pytest-cov` for coverage; contract tests under `code/tests/contract/`.
- **Target Platform**: Linux (GitHub Actions runner)  
- **Project Type**: Library + CLI (`code/src/cli/run_detection.py`)  
- **Performance Goals**: Process ≥10 k observations per minute on a single‑core VM; ELBO convergence within a predefined number of iterations.  
- **Constraints**: `code/config.yaml` < 2 KB; all raw data immutable; reproducible seeds pinned in config.

## Constitution Check
| Principle | Requirement | How the plan satisfies it |
|-----------|-------------|---------------------------|
| **I. Reproducibility** | Pin all random seeds; deterministic data download URLs; CI script re‑runs entire pipeline. | `code/config.yaml` contains `seed: 42`; data download scripts use ucimlrepo loader for deterministic access; GitHub Actions workflow defined in `.github/workflows/ci.yml`. |
| **II. Verified Accuracy** | No external citation without validator confirmation. | UCI datasets fetched via ucimlrepo loader (canonical source). The ucimlrepo loader IS the verified canonical access method—Principle II's citation verification applies to paper/technical-design citations, not to dataset access methods. No unverified URLs cited. Anomaly injection parameters documented in config.yaml. |
| **III. Data Hygiene** | Checksums recorded; raw data never overwritten. | `state/projects/PROJ-024-...yaml` will store SHA256 hashes for each raw file; transformations write to new files under `data/processed/`. |
| **IV. Single Source of Truth** | Every figure/metric traced to a data row & code block. | Evaluation scripts emit JSON with provenance fields (`data_file`, `code_line`). The paper generation step pulls directly from these JSON artefacts. |
| **V. Versioning Discipline** | Content hashes for all artefacts; state file timestamp updated on change. | CI step computes hashes via `sha256sum`; updates `state/projects/...yaml` with `updated_at`. |
| **VI. Numerical Stability & Convergence** | ELBO logs recorded; non‑convergent runs flagged. | ELBO values written to `logs/elbo/` each iteration; a post‑run validator aborts if ELBO improvement < 1e‑4 after 500 steps. |
| **VII. Prior Sensitivity Analysis** | Vary DP concentration and report robustness. | Sensitivity script `code/src/analysis/prior_sensitivity.py` sweeps `alpha` and `gamma`; results stored in `data/processed/results/prior_sensitivity.json`. |
| **VIII. (Implicit) Project Governance** | All changes go through PR & CI. | Standard GitHub workflow enforced. |

## Project Structure
```text
specs/001-bayesian-nonparametrics-for-anomaly-dete/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── dataset.schema.yaml
    ├── anomaly_score.schema.yaml
    ├── evaluation_metrics.schema.yaml
    ├── threshold_calibrator.schema.yaml
    ├── anomaly_detector.schema.yaml
    ├── dpgmm.schema.yaml
    ├── streaming_dpgmm.schema.yaml
    ├── anomaly_detector_service.schema.yaml
    ├── threshold_calibrator_service.schema.yaml
    └── time_series_dataset.schema.yaml

code/
├── src/
│   ├── models/
│   │   └── dpgmm.py
│   ├── services/
│   │   ├── anomaly_detector.py
│   │   └── threshold_calibrator.py
│   ├── data/
│   │   └── download_datasets.py
│   ├── evaluation/
│   │   └── metrics.py
│   ├── analysis/
│   │   ├── prior_sensitivity.py
│   │   └── plot_results.py
│   ├── baselines/
│   │   └── arima.py
│   ├── cli/
│   │   └── run_detection.py
│   └── utils/
│       └── logger.py
├── tests/
│   ├── contract/
│   │   ├── test_dataset_schema.py
│   │   ├── test_anomaly_score_schema.py
│   │   ├── test_evaluation_metrics_schema.py
│   │   ├── test_threshold_calibrator_schema.py
│   │   ├── test_anomaly_detector_schema.py
│   │   ├── test_dpgmm_schema.py
│   │   ├── test_streaming_dpgmm_schema.py
│   │   ├── test_anomaly_detector_service_schema.py
│   │   └── test_threshold_calibrator_service_schema.py
│   ├── unit/
│   │   └── test_anomaly_detector.py
│   └── integration/
│       └── test_end_to_end.py
├── config.yaml          # <2 KB, hyper‑params & seeds only
└── requirements.txt

data/
├── raw/
│   ├── electricity.csv
│   ├── traffic.csv
│   └── synthetic_control.csv
└── processed/
    └── results/
        ├── model_checkpoints/
        ├── evaluation_metrics.json
        ├── prior_sensitivity.json
        └── figures/

state/
└── projects/
    └── PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml

logs/
└── elbo/
    └── dpgmm_elbo.log
```

**Structure Decision**: Single‑project layout (Option 1) with a clear `code/src/` package hierarchy; all tests live under `code/tests/` as required by the spec.

**Test Schema Alignment Note**: Spec.md requires multiple total contract test files (6 schema tests + 2 service interface tests). The 9 schema files above include time_series_dataset.schema.yaml which serves as the master dataset schema; the 6 core schema tests are: dataset, anomaly_score, evaluation_metrics, threshold_calibrator, anomaly_detector, dpgmm. The streaming_dpgmm schema validates the StreamingDPGMM wrapper configuration. The 2 service interface tests cover AnomalyDetectorService and ThresholdCalibratorService.

## Implementation Phases & Ordering
| Phase | Description | Key Outputs | Dependencies |
|-------|-------------|-------------|--------------|
| **0 – Research** | Literature review, define priors, select datasets, specify anomaly injection methodology. | `research.md`, `data-model.md` | – |
| **1 – Data Acquisition** | Download UCI Electricity, Traffic, Synthetic Control CSVs via ucimlrepo; compute SHA256 checksums; store under `data/raw/`; apply temporal preprocessing (lag features, rolling stats). | `state/projects/...yaml` (artifact_hashes), raw CSVs, processed CSVs | Phase 0 |
| **2 – Model Development** | Implement DPGMM with Pyro ADVI; expose `AnomalyDetectorService` API; add checkpointing; implement `StreamingDPGMM` wrapper for sliding-window updates. | `code/src/models/dpgmm.py`, `code/src/services/anomaly_detector.py` | Phase 1 |
| **3 – Threshold Calibration** | Implement `ThresholdCalibratorService` (percentile‑based, adaptive). | `code/src/services/threshold_calibrator.py` | Phase 2 |
| **4 – Evaluation & Metrics** | Compute F1, precision, recall, AUC‑ROC on synthetic test set with injected anomalies; log ELBO convergence on original data (unsupervised). | `data/processed/results/evaluation_metrics.json`, ELBO logs | Phases 2‑3 |
| **5 – Prior Sensitivity** | Run sweep over `alpha`/`gamma`; store results. | `data/processed/results/prior_sensitivity.json` | Phase 4 |
| **6 – Contract & Test Suite** | Create JSON‑Schema contracts; write corresponding contract test files; achieve ≥80 % coverage. | `contracts/*.schema.yaml`, `code/tests/contract/` | Phases 2‑5 |
| **7 – Documentation & Quickstart** | Write `quickstart.md`; generate figures from results; ensure all artefacts traceable. | `quickstart.md`, figure PNGs | Phases 4‑6 |
| **8 – Cleanup & Verification (Phase 9.5‑9.6)** | Verify filesystem layout (T240-T245), config size (<2KB), checksum integrity, log ELBO, run contract test coverage, document commands. | Command‑line evidence scripts (`scripts/verify.sh`) | All previous phases |
| **9 – Final Acceptance (T145)** | Run full CI pipeline; ensure all success criteria SC‑001 – SC‑006 satisfied. | CI badge, acceptance report | Phase 8 |

**Phase Ordering Notes**:
- Data download (Phase 1) precedes model development (Phase 2).
- Contracts (Phase 6) precede documentation (Phase 7) that references them.
- Evaluation metrics (Phase 4) precede sensitivity analysis (Phase 5).

**Data Split Strategy**: A majority portion for training (unsupervised), [deferred] threshold calibration (unsupervised), [deferred] supervised evaluation with injected anomalies. This separates US3 (unsupervised threshold) from F1 computation (supervised).

**Config.yaml Size Enforcement**: The `code/config.yaml` file MUST remain under 2KB (2048 bytes). Only hyperparameters, random seeds, and base paths are permitted. Derived statistics, checksums, and computed values MUST be stored in `state/projects/PROJ-024-...yaml`. Violation of this constraint will be caught by T243 verification task and block Phase 9.5 completion.

**Directory Structure Enforcement**: The following directories are FORBIDDEN and must not exist:
- `data/results/` (legacy; all results must be in `data/processed/results/`)
- `data/raw/raw/` (nested raw directories)
- `data/raw/pems_sf*` (PEMS-SF files per SC-004)

All violations will be caught by T240-T242 verification tasks.