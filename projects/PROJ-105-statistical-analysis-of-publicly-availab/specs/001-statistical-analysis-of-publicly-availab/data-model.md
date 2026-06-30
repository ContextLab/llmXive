# Data Model: Flight Delay Analysis

## 1. Entity Definitions

### 1.1 DelayRecord
Represents a single flight event after pre-processing.
- **Attributes**:
  - `flight_id` (str): Unique identifier (e.g., `Carrier + FlightNum + Date`).
  - `total_delay_minutes` (float): Sum of arrival and departure delays. Must be $\ge 0$.
  - `carrier` (str): Airline carrier code.
  - `origin` (str): Origin airport code.
  - `destination` (str): Destination airport code.
  - `is_anomaly` (bool): True if `total_delay_minutes > 1440`.

### 1.2 DistributionModel
Represents a fitted parametric distribution.
- **Attributes**:
  - `name` (str): Name of the distribution (e.g., "Log-Normal").
  - `parameters` (dict): MLE estimates (e.g., `{"s": 1.2, "loc": 0.5}`).
  - `metrics` (dict): Goodness-of-fit scores (`{"aic": 1234.5, "bic": 1240.0, "ks_stat": 0.05, "ad_stat": 2.1, "tail_ks_stat": 0.02, "tail_ks_p_value": 0.15, "x_min": 60.0}`).
  - `converged` (bool): Whether the MLE optimization succeeded.
  - `is_valid_tail` (bool): Whether the model passed the Tail Validity Gate (Tail KS p > 0.05 and Hill stable).

### 1.3 TailIndexEstimate
Represents the heavy-tail diagnostic result.
- **Attributes**:
  - `method` (str): "Hill".
  - `threshold_k` (int): Number of records used for estimation.
  - `estimated_alpha` (float): Tail index (shape parameter).
  - `confidence_interval` (list): [lower, upper] bounds.
  - `stability_range` (str): Description of the k-range where the estimate was stable.
  - `x_min_used` (float): The threshold above which the Hill estimator was applied.
  - `loglog_r_squared` (float): R² of the log-log survival plot.
  - `is_power_law` (bool): True if R² >= 0.95 and stable.

## 2. Data Flow

1. **Input**: Raw BTS CSV/Parquet (External).
2. **Process**: `cleaning.py` -> **Intermediate**: `cleaned_delays.parquet` (DelayRecord set).
   - **Split**: `dataset_all` (includes 0s) and `dataset_positive` (delay > 0).
3. **Process**: `fitting.py` -> **Intermediate**: `model_results.json` (DistributionModel list).
4. **Process**: `diagnostics.py` -> **Output**: `tail_analysis.json` (TailIndexEstimate) + Plot images.
5. **Process**: `state_manager.py` -> **Output**: Updated `state/` file.

## 3. Storage Schema

- **Raw Data**: `data/raw/bts_2022.parquet` (Immutable, checksummed).
- **Processed Data**: `data/processed/delays_cleaned.parquet` (Derived).
- **Results**: `output/results.json` (Aggregated model metrics and tail estimates).
- **Artifacts**: `output/plots/` (Log-log survival, QQ-plots, Hill stability).
