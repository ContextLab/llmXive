# API Documentation

## Scoring Module (`code/scoring/`)

### `sart.py`
- `score_sart_trial(trial: dict) -> dict`: Score a single SART trial.
 - Input: `{'response_time': float, 'accuracy': bool, 'stimulus_type': str}`
 - Output: `{'commission_errors': int, 'omission_errors': int, 'mean_rt': float}`
- `score_sart_session(trials: List[dict]) -> dict`: Score a full SART session.

### `ospan.py`
- `score_ospan_trial(trial: dict) -> dict`: Score a single Ospan trial.
 - Input: `{'stimulus': str, 'recall': str, 'accuracy': bool}`
 - Output: `{'correct': bool}`
- `score_ospan_session(trials: List[dict]) -> dict`: Score a full Ospan session.
 - Output: `{'span_score': int, 'total_correct': int}`

### `questionnaires.py`
- `score_pss10_session(responses: List[int]) -> dict`: Score PSS-10.
 - Input: List of 10 responses (1-4)
 - Output: `{'total_score': int}`
- `score_panas_session(responses: Dict[str, List[int]]) -> dict`: Score PANAS.
 - Input: Dict with 'positive' and 'negative' keys, each a list of 10 responses (1-5)
 - Output: `{'positive_affect': int, 'negative_affect': int}`

### `id_generator.py`
- `validate_id_format(participant_id: str) -> bool`: Check if ID matches `P\d{3}`.
- `generate_sequence_ids(n: int) -> List[str]`: Generate a list of P001, P002,...
- `IDGenerator`: Class to manage ID generation from a source.

## Analysis Module (`code/analysis/`)

### `bootstrap_ci.py`
- `calculate_bootstrap_ci(data: List[float], n_resamples: int = 10000) -> BootstrapResult`:
 - Returns: `{'mean': float, 'ci_lower': float, 'ci_upper': float, 'std': float}`
- `run_bootstrap_analysis(pre_data: List[float], post_data: List[float]) -> Dict`:
 - Returns bootstrap results for change scores.

### `change_scores.py`
- `calculate_change_score(pre: float, post: float) -> float`: post - pre
- `calculate_change_scores_for_participant(participant_data: Dict) -> Dict`:
 - Returns change scores for all metrics for a participant.

### `effect_sizes.py`
- `calculate_cohens_d(pre: List[float], post: List[float]) -> float`: Cohen's d.
- `calculate_effect_sizes_for_metric(metric_name: str) -> EffectSizeResult`:
 - Returns effect size with CI.

### `holm_bonferroni.py`
- `calculate_holm_bonferroni(p_values: List[float]) -> HolmBonferroniResult`:
 - Returns corrected p-values and significance flags.

### `power_simulation.py`
- `run_power_simulation(n_iterations: int = 1000) -> Dict`:
 - Returns power estimate for detecting d=0.5 with Holm-Bonferroni correction.

### `statistical_summary.py`
- `aggregate_results() -> Dict`: Aggregate all analysis results into a summary.

### `wilcoxon_fallback.py`
- `run_wilcoxon_test(pre: List[float], post: List[float]) -> WilcoxonResult`:
 - Fallback test if bootstrap fails.

## Compliance Module (`code/compliance/`)

### `parse_logs.py`
- `parse_logs(log_files: List[str]) -> List[Dict]`: Parse JSON or CSV logs.

### `rules_engine.py`
- `check_compliance_rules(log: Dict) -> ComplianceResult`:
 - Checks: social media ≤30 min, no news, notifications off.

### `flag_non_compliant.py`
- `flag_non_compliant_day(log: Dict) -> bool`: Flag if rules violated.

## Pipeline Module (`code/pipeline/`)

### `merge_data.py`
- `merge_baseline_post(baseline_path: str, post_path: str) -> Dict`:
 - Merge baseline and post-intervention data by participant ID.

### `aggregate_compliance.py`
- `calculate_daily_scores(logs: List[Dict]) -> Dict`: Daily compliance scores.
- `calculate_weekly_scores(daily_scores: Dict) -> Dict`: Weekly aggregates.

## Validation Module (`code/validation/`)

### `synthetic_baseline.py`
- `generate_synthetic_data(n_participants: int = 100) -> List[Dict]`:
 - Generates synthetic data with specified distributions.
- `write_csv(data: List[Dict], output_path: str)`: Write to CSV.

### `validate_success_criteria.py`
- `validate_success_criteria(summary: Dict) -> ValidationResult`:
 - Checks p < 0.05, d ≥ 0.2, and effect direction.

## Visualization Module (`code/viz/`)

### `generate_plots.py`
- `generate_all_plots(change_scores: Dict)`:
 - Creates boxplots and change score distributions.
 - Outputs to `results/`.

## Config Module (`code/config/`)

### `env_config.py`
- `get_config() -> ProjectConfig`: Load configuration from environment.
- `get_path(key: str) -> Path`: Get a specific path.
- `get_param(key: str) -> Any`: Get a specific parameter.
