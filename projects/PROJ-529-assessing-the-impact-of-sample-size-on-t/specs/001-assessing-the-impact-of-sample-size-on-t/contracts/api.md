# API Contracts

## Internal Interfaces

### `code/download.py`
- `fetch_cochrane_data() -> list[dict]`
- `generate_simulation_data(params: dict) -> list[dict]`

### `code/subsample.py`
- `generate_subsamples(meta_data: MetaAnalysis, k_values: list[int], n_iterations: int) -> list[Subsample]`

### `code/models.py`
- `fit_model(effects: list[float], ses: list[float], method: str) -> dict`
- `calculate_coverage(subsamples: list[Subsample], full_sample_estimate: float) -> float`

### `code/metrics.py`
- `compute_stability(subsamples: list[Subsample], k: int) -> float`
- `aggregate_metrics(all_subsamples: list[Subsample]) -> list[StabilityMetric]`

### `code/analysis.py`
- `fit_gam_model(metrics: list[StabilityMetric]) -> dict`
- `detect_threshold(gam_model: dict, threshold_derivative: float) -> int`
