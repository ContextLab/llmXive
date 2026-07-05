# Data Model: Assessing the Impact of Sample Size on Meta-Analytic Reliability

## Entities

### MetaAnalysis
- meta_id: str (unique identifier)
- title: str
- source: str (Cochrane, Campbell, or Simulation)
- total_studies: int
- effect_sizes: List[float]
- standard_errors: List[float]
- pooled_effect: Optional[float]
- pooled_se: Optional[float]
- model_type: Optional[str] (FE or RE)

### Subsample
- subsample_id: str
- meta_id: str
- k: int (number of studies in subsample)
- seed: int
- effect_sizes: List[float]
- standard_errors: List[float]
- pooled_effect: float
- pooled_se: float
- model_type: str (FE or RE)
- estimator: str (DL, REML, etc.)

### StabilityMetric
- metric_id: str
- meta_id: str
- k: int
- sd_effects: float (standard deviation of pooled effects across subsamples)
- coverage_rate: float (proportion of CIs containing full-sample estimate)
- nominal_coverage: float (target coverage rate, e.g., 0.95)
- threshold_detected: bool