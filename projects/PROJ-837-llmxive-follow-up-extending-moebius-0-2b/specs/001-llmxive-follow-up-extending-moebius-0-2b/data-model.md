# Data Model Specification

## Entities

### MaskedRegion
Represents a specific masked area within an image.
- `image_id`: str (Unique identifier)
- `mask_path`: str (Path to binary mask)
- `mask_complexity_score`: float (Ground truth or proxy score 1-5)
- `gradient_variance`: float (Synthetic metric)
- `texture_entropy`: float (Synthetic metric)
- `mask_coverage`: float (Ratio of masked pixels)

### InferenceResult
Output of the Moebius-Dynamic model.
- `image_id`: str
`predicted_rank`: int (1-5)
- `inference_time_ms`: float
- `reconstruction_loss`: float
- `fid_score`: float
- `lpps_score`: float

### GatingState
Internal state of the gating mechanism.
- `complexity_input`: float (Normalized 0.0-1.0)
- `predicted_rank`: int
- `rank_modulation_factor`: float
- `fallback_triggered`: bool (True if mask coverage > 50%)

## File Formats

### CSV: `data/annotations/decoupled_scores.csv`
Columns: `image_id`, `score`, `mode`, `rater_id` (optional)
- `score`: Integer 1-5.
- `mode`: "CI" or "RESEARCH".

### JSON: `data/results/proxy_validation.json`
Structure:
```json
{
 "correlation_coefficient": 0.0,
 "p_value": 0.0,
 "gate_status": "BLOCKED" | "PASSED" | "EXPECTED_LOW_CORRELATION",
 "mode": "CI" | "RESEARCH"
}
```

### JSON: `data/results/evaluation_report.json`
Structure:
```json
{
 "dynamic_latency_ms": 0.0,
 "static_latency_ms": 0.0,
 "latency_reduction_pct": 0.0,
 "fid_delta": 0.0,
 "power_analysis": {
 "power": 0.0,
 "status": "UNDERPOWERED" | "ADEQUATE"
 }
}
```
