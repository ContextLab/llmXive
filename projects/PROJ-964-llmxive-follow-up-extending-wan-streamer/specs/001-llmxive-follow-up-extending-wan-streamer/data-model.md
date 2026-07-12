# Data Model: llmXive follow-up: extending "Wan-Streamer v0.1"

## 1. Overview

This document defines the data structures used throughout the `001-llmxive-streamer-optimization` feature. All data flows from `raw` (logs) to `processed` (Parquet) to `artifacts` (model checkpoints, metrics logs).

**Canonical Schemas**: The system validates against exactly three schema files in `contracts/`:
1. `dataset.schema.yaml`
2. `estimator_output.schema.yaml`
3. `metrics.schema.yaml`
All other schema files in `contracts/` are deprecated and must be ignored.

## 2. Data Flow

```mermaid
graph TD
    A[Raw Source: Wan-Streamer Logs] -->|FR-001, FR-019, FR-022| B(Extract Data Task)
    B -->|Output: processed/turn_events.parquet| C[Data Model: TurnEvent]
    C -->|FR-002| D[Train Estimator Task]
    D -->|Output: processed/estimator_checkpoint.pt| E[Estimator Model]
    E -->|FR-003, FR-008| F[Simulate Inference Task]
    F -->|Output: processed/hybrid_metrics.parquet| G[Data Model: HybridMetrics]
    G -->|FR-005, FR-010| H[Analyze Latency Bias Task]
    H -->|Output: results/statistical_report.yaml| I[Final Artifacts]
    F -->|FR-008, FR-009| J[Execute Fallback Task (Counterfactual Re-run)]
    J -->|Output: processed/counterfactual_full.parquet| K[Counterfactual Ground Truth]
    K -->|FR-010| H
```

## 3. Entity Definitions

### 3.1 TurnEvent (Input/Processed)
Represents a single frame or short segment with turn-taking context.
*   **Source**: Extracted from `raw` logs.
*   **Schema**: See `contracts/dataset.schema.yaml`.
*   **Key Fields**:
    *   `timestamp`: Float (seconds from start).
    *   `turn_label`: String (`"interruption"`, `"pause"`, `"normal"`).
    *   `semantic_feature`: Float vector (embedded text).
    *   `prosodic_feature`: Float vector (energy, pitch).
    *   `latent_delta_magnitude`: Float (ground truth $||\Delta z||$).
    *   `is_randomized_skip`: Boolean (set by FR-008).

### 3.2 EstimatorOutput (Intermediate)
Output of the lightweight model during inference.
*   **Source**: `code/tasks/train_estimator.py` (training) / `simulate_inference.py` (inference).
*   **Schema**: See `contracts/estimator_output.schema.yaml`.
*   **Key Fields**:
    *   `predicted_delta`: Float (predicted magnitude).
    *   `uncertainty_score`: Float (0.0 to 1.0).
    *   `action`: String (`"skip"`, `"full_solver"`).

### 3.3 HybridMetrics (Output)
Aggregated metrics for the hybrid pipeline.
*   **Source**: `code/tasks/analyze_latency_bias.py`.
*   **Schema**: See `contracts/metrics.schema.yaml`.
*   **Key Fields**:
    *   `fid_baseline`: Float.
    *   `fid_hybrid`: Float.
    *   `latency_baseline_ms`: Float.
    *   `latency_hybrid_ms`: Float.
    *   `tost_p_value`: Float.
    *   `correlation_r`: Float.

## 4. File Formats

*   **Input/Intermediate**: Parquet (optimized for CPU read/write, columnar).
*   **Model Checkpoints**: `.pt` (PyTorch CPU).
*   **Reports**: YAML (structured, human-readable).
*   **Checksums**: `sha256sum` format in `data/checksums.txt`.

## 5. Constraints & Validation

*   **Immutability**: Raw data is never modified. Derivations create new files.
*   **Size Limit**: `processed` data ≤ 1 GB.
*   **Schema Enforcement**: All Parquet files must pass validation against `contracts/dataset.schema.yaml`, `contracts/estimator_output.schema.yaml`, and `contracts/metrics.schema.yaml` (the **canonical** schemas) before being consumed by the next task.
*   **Missing Data**: If `human_mos` is missing, the `validate_proxy_mos` task logs the specific assumption string (FR-024).
*   **Contract Linking**: This document and `quickstart.md` explicitly link to the canonical schemas in `contracts/` as per FR-021.