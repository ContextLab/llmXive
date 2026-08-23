# Data Model: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## 1. Entity Definitions

### 1.1 DiscreteStateVector
Represents the quantized state of the embodied agent at a single time step.
- **Fields**:
  - `timestamp` (float): Unix timestamp or relative step index.
  - `position` (list[float] or list[int]): Quantized end-effector position.
  - `orientation` (list[float] or list[int]): Quantized orientation (if applicable).
  - `velocity` (list[float] or list[int]): Derived velocity (continuous derivation, then quantized). **Note**: Stored as `number` (float) for continuous baseline context, `integer` for discrete.
  - `collision_flags` (list[int]): Binary flags for collision events.
  - `is_dropped` (bool): True if state was dropped due to 1-bit collapse.
  - `metadata` (dict): Source schema mapping info.

### 1.2 PredictionHorizon
Defines the forecasting scope.
- **Values**: 100, 500, 1000 time steps.

### 1.3 ErrorMetric
Composite record for statistical analysis.
- **Fields**:
  - `mse_discrete` (float): Total MSE for discrete modality (normalized by D).
  - `mse_continuous` (float): Total MSE for continuous baseline (normalized by D).
  - `mse_ratio` (float): `mse_discrete / mse_continuous`.
  - `cumulative_error_rate` (float): Slope of MSE vs. time.
  - `p_value` (float): Statistical significance from LMM.
  - `is_significant` (bool): True if p < 0.05.
  - `stability_claim_framing` (string): "mse_ratio" or "relative_degradation".

### 1.4 StabilityThreshold
The identified boundary where stability is lost.
- **Fields**:
  - `quantization_level` (int): Bit depth (4, 6, 8, 16).
  - `noise_level` (float): Standard deviation multiplier.
  - `mse_ratio_ci_upper` (float): Upper bound of 95% CI.
  - `threshold_reached` (bool): True if CI upper bound > 1.0.

### 1.5 PowerAnalysisResult
Result of the a priori power analysis.
- **Fields**:
  - `effect_size` (float): Cohen's d (target 0.5).
  - `power` (float): Target power (0.8).
  - `alpha` (float): Significance level (0.05).
  - `n_runs` (int): Calculated required number of runs.
  - `method` (string): "LMM_simulation".

## 2. Data Flow

1. **Raw Input**: `lerobot/libero_plus` (Parquet) -> `observations.positions`, `observations.ee_pos`.
2. **Verification**: Check schema keys. Fail if missing.
3. **Derivation**: Continuous velocity/acceleration calculated.
4. **Noise Injection**: Gaussian noise added to continuous values.
5. **Quantization**: Mapping to discrete integers.
6. **Validation**: 1-bit collapse check.
7. **Model Input**: Discrete JSON vectors fed to Kairos.
8. **Output**: Predicted sequences -> MSE calculation (normalized) -> LMM analysis.

## 3. Storage Format

- **Raw Data**: Parquet (downloaded to `data/raw/`).
- **Processed Data**: JSON Lines (`.jsonl`) or JSON arrays in `data/processed/`.
- **Results**: JSON (`results/stats_results.json`, `results/power_analysis_report.json`).