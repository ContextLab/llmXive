# Data Model: Extending TriSplat for CPU-only Edge Robotics

## Entities

### SceneResult
Represents the outcome of a single scene reconstruction.
- `scene_id` (str): Unique identifier for the scene (e.g., "scene_001").
- `view_count` (int): Number of input views used (2, 3, 4, or 5).
- `latency` (float): Inference time in seconds.
- `chamfer_distance` (float): Geometric error metric.
- `psnr` (float): Photometric quality metric.
- `status` (str): "success", "timeout", "low_texture", "monocular_skipped".
- `error_flag` (str or null): Specific error code if failed (e.g., "TIMEOUT_CONVERGENCE_FAILED").

### ThresholdResult
Result of the sparsity threshold analysis.
- `threshold_view_count` (int): The view count where error exceeds tolerance.
- `relative_error_increase` (float): Calculated as `(error_N - error_baseline) / error_baseline`.
- `tolerance` (float): The configured tolerance threshold (default 0.15).
- `method` (str): Statistical method used (e.g., "Wilcoxon").

### BenchmarkData
Aggregated data for trade-off analysis.
- `view_count` (int): Number of input views.
- `latency` (float): Average latency for geometry-only model.
- `chamfer_distance` (float): Average Chamfer Distance.
- `psnr` (float): Average PSNR.
- `baseline_latency` (float): Average latency for baseline TriSplat.
- `speedup_ratio` (float): `baseline_latency / latency`.

### ChecksumRecord
Record for data integrity verification.
- `file_path` (str): Relative path to the artifact.
- `sha256` (str): SHA-256 hash of the file content.
- `file_size` (int): File size in bytes.

## File Formats

### JSON (Batch Results)
```json
[
 {
 "scene_id": "scene_001",
 "view_count": 3,
 "latency": 120.5,
 "chamfer_distance": 0.045,
 "psnr": 28.3,
 "status": "success",
 "error_flag": null
 }
]
```

### CSV (Benchmark Report)
```csv
view_count,latency,chamfer_distance,psnr,baseline_latency,speedup_ratio
2,150.2,0.052,27.1,300.5,2.0
3,135.8,0.045,28.3,290.1,2.13
```

### YAML (State File)
```yaml
project_id: PROJ-938-llmxive-follow-up-extending-trisplat-sim
artifacts:
 - path: data/processed/threshold_result.json
 sha256: abc123...
 size: 1024
 - path: data/processed/benchmark_tradeoff.csv
 sha256: def456...
 size: 2048
```
