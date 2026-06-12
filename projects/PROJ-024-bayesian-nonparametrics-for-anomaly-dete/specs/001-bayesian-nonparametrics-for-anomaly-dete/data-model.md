# Data Model: Bayesian Nonparametrics for Anomaly Detection in Time Series

## Core Entities
| Entity | Description | Primary Attributes |
|--------|-------------|--------------------|
| **Dataset** | Raw univariate time‑series used for training/evaluation. | `series_id` (string), `values` (list float, ≥ 1000), optional `timestamp` (list datetime) |
| **AnomalyScore** | Score produced for a single observation. | `score` (float), `timestamp` (datetime), optional `uncertainty` (float) |
| **EvaluationMetrics** | Quantitative performance indicators. | `f1_score`, `precision`, `recall` (float, required), `auc_roc` (float, optional) |
| **ThresholdCalibrator** | Calibration artefact linking score distribution to decision boundary. | `threshold` (float), `percentile` (float), `adaptive` (bool) |
| **AnomalyDetector** | Configuration of the DPGMM model. | `model_type` (e.g., `"DPGMM"`), optional `n_components` (int), `convergence_threshold` (float) |
| **DPGMM** | Hyper‑parameters of the Dirichlet Process mixture. | `alpha` (float), `gamma` (float), `concentration_prior` (float) |
| **StreamingDPGMM** | Wrapper for sliding-window updates (addresses temporal autocorrelation). | `window_size` (int, default 1000), `update_frequency` (int, default 100), `lag_features` (list int), `alpha` (float), `gamma` (float) |
| **AnomalyDetectorService** | Service interface exposing detection API. | `service_name` (string), `method_count` = 7, `type_hints_compliant` (bool) |
| **ThresholdCalibratorService** | Service interface for threshold management. | `service_name` (string), `method_count` = 6, `type_hints_compliant` (bool) |

## Relationships
- A **Dataset** feeds many **AnomalyScore** records via `AnomalyDetectorService.process_stream`.
- **AnomalyDetectorService** holds a **DPGMM** model configured by **AnomalyDetector** or **StreamingDPGMM** wrapper.
- **ThresholdCalibratorService** consumes a list of **AnomalyScore** to produce a **ThresholdCalibrator**.
- **EvaluationMetrics** are computed by comparing **AnomalyScore** (after thresholding) against ground‑truth labels (synthetic anomalies injected for supervised eval).

## Temporal Preprocessing
- Lag features: lag-1, lag-7 applied to raw observations.
- Rolling statistics: mean and std over 50-observation window.
- These features address autocorrelation and non-stationarity concerns (Principle VI).

## Persistence
- Raw CSVs remain immutable under `data/raw/`.  
- Processed artefacts (model checkpoints, metrics, figures) live under `data/processed/`.  
- Checksums and derived statistics are stored in `state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-detection.yaml`.  

All entities are validated against the JSON‑Schema contracts located in `specs/contracts/`.

---