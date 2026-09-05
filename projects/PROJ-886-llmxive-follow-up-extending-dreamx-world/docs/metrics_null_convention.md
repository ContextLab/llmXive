# Metrics Null Convention Documentation

## Reconciliation of Spec FR-004 and Plan Phase 2

### Background

Spec FR-004 originally required a "sentinel value" for divergent trajectories.
However, Plan Phase 2 established that `null` is the preferred convention to
ensure statistical validity in downstream analysis (e.g., Wilcoxon signed-rank test).

### Decision

We have reconciled these requirements by:

1. **Using `null` (empty string in CSV) for divergent trajectories**:
 - `mae_position`: `null` when SfM fails
 - `mae_rotation`: `null` when SfM fails
 - `scale_drift`: `null` when SfM fails
 - `convergence`: `false` when SfM fails

2. **Logging the exception**:
 - Every write operation logs the reconciliation decision
 - Format: "Reconciling Spec FR-004 'sentinel value' with Plan 'null' convention: Using empty string (None) for divergent trajectories to ensure statistical validity."

3. **Maintaining statistical validity**:
 - Downstream analysis (e.g., `code/analysis/stats.py`) filters for `convergence=true`
 - This ensures only valid trajectories are included in statistical tests
 - Null values are properly handled in pandas/numpy operations

### CSV Schema

| Column | Type | Null Allowed | Description |
|--------|------|--------------|-------------|
| trajectory_id | str | No | Unique identifier |
| model | str | No | Model name (e.g., "dreamx_lite") |
| mae_position | float | Yes | Mean Absolute Error for position (null if SfM failed) |
| mae_rotation | float | Yes | Mean Absolute Error for rotation (null if SfM failed) |
| convergence | bool | No | True if SfM converged, False otherwise |
| sfm_failure_reason | str | Yes | Exact failure reason from COLMAP (empty if success) |
| scale_drift | float | Yes | Ratio of mean depths (null if SfM failed) |

### Example Data

```csv
trajectory_id,model,mae_position,mae_rotation,convergence,sfm_failure_reason,scale_drift
traj_001,dreamx_lite,0.123,0.045,true,,1.02
traj_002,dreamx_lite,,,false,insufficient_features,
traj_003,dreamx_lite,0.089,0.032,true,,0.98
```

### Implementation Details

- **Writer**: `code/analysis/metrics_writer.py` converts `None` to empty string
- **Reader**: `code/analysis/metrics_writer.py` converts empty string back to `None`
- **Logging**: Exception is logged at `INFO` level during write operations

### Exception Log Entry

When `write_metrics_csv()` is called with `log_exception=True` (default), the following
log entry is produced:

```
Reconciling Spec FR-004 'sentinel value' with Plan 'null' convention: Using empty string (None) for divergent trajectories to ensure statistical validity.
```

This ensures traceability and compliance with both Spec FR-004 and Plan Phase 2.
