# API Contracts and Interfaces

## Data Acquisition Interface
**Module**: `code/download.py`
- `fetch_meta_analyses() -> List[MetaAnalysis]`
 - Fetches real data from Cochrane/Campbell.
 - Raises `DataAcquisitionError` if fetch fails or count < 50.
- `generate_simulation_data() -> List[MetaAnalysis]`
 - Fallback method generating data based on Ioannidis parameters.

## Subsampling Interface
**Module**: `code/subsample.py`
- `generate_subsamples(meta: MetaAnalysis, k_range: List[int], max_iter: int = 100) -> List[Subsample]`
 - Generates bootstrap subsamples.
 - Logs seeds and iteration details.

## Modeling Interface
**Module**: `code/models.py`
- `fit_model(effect_sizes, se, estimator_type) -> ModelResult`
 - Fits FE or RE model.
 - Handles zero-variance and negative variance edge cases.
- `calculate_coverage(subsamples, full_estimate) -> float`
 - Computes CI coverage rate.

## Analysis Interface
**Module**: `code/analysis.py`
- `fit_stability_curve(metrics_df) -> GAMResult`
 - Fits GAM to stability metrics.
 - Returns changepoint estimate.
- `detect_threshold(gam_result, nominal_coverage) -> Dict`
 - Identifies minimum k for stable coverage.

## Visualization Interface
**Module**: `code/viz.py`
- `plot_stability_curve(metrics_df, output_path)`
- `plot_coverage_rate(metrics_df, output_path)`
