# Data Model

## Raw Results Schema (energy_results_raw.csv)
- model_id: str
- problem_id: str
- tokens_generated: int
- energy_kwh: float
- runtime_seconds: float
- pass_fail_status: int (0/1)

## Aggregated Results Schema (energy_results_aggregated.csv)
Same as raw, but filtered for non-null energy and tokens > 0.

## Stats Report Schema (stats_report.csv)
- metric: str
- value: float
- model_id: str (optional)
