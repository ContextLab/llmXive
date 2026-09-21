# Data Model Specification

## Entities

### SceneResult
Represents the outcome of a single scene reconstruction.

```yaml
scene_id: string
view_count: integer (2-5)
status: string (success, skipped, failed)
chamfer_distance: float (optional)
psnr: float (optional)
latency: float (seconds)
error_flag: string (optional, e.g., "LOW_TEXTURE_CONVERGENCE_FAILED")
timestamp: string (ISO 8601)
```

### ThresholdResult
Represents the identified sparsity threshold.

```yaml
threshold_view_count: integer
tolerance_threshold: float (0.15)
relative_error_increase: float
method: string ("t-test" or "wilcoxon")
p_value: float
```

### BenchmarkResult
Represents comparative benchmark metrics.

```yaml
view_count: integer
latency: float
chamfer_distance: float
psnr: float
baseline_latency: float (optional)
speedup_ratio: float
psnr_delta: float
```

## Relationships

- A `BatchRun` produces multiple `SceneResult` entities.
- `SceneResult` entities are aggregated into `ThresholdResult`.
- `SceneResult` entities are compared to generate `BenchmarkResult`.
