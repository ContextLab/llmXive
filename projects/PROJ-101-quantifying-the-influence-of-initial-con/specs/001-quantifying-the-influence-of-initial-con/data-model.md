# Data Model: Quantifying the Influence of Initial Conditions on Chaotic Systems

## Entities

### Trajectory
A time-ordered sequence of state vectors representing the system's evolution in phase space.
- **Attributes**:
  - `id`: Unique identifier (UUID).
  - `system_params`: Dictionary of $N$, $\sigma$, $\rho$, $\beta$, coupling strength.
  - `noise_level`: $\sigma_{noise}$ (float).
  - `seed`: Random seed (int).
  - `data`: Array of shape $(T_{total}, 3N)$ containing state vectors.
  - `is_physical`: Boolean (True if trajectory remains bounded within simulation time).
  - `escape_time`: Float (Time step at which trajectory exits basin, or `null` if bounded).
  - `shadowing_valid`: Boolean (Diagnostic only; True if shadowing check passes, recorded but not used for filtering).

### FTLE Estimate
A calculated scalar value representing the average exponential rate of divergence over a specific finite time window.
- **Attributes**:
  - `trajectory_id`: Reference to parent trajectory.
  - `window_size`: $T$ (int).
  - `start_time`: Start index of window.
  - `max_exponent`: $\lambda_{max}$ (float).
  - `full_spectrum`: List of $3N$ exponents (list[float]).
  - `deviation`: $\Delta \lambda = \lambda_{max} - \lambda_{asymptotic}$ (float).
  - `noise_level`: $\sigma_{noise}$ (float).
  - `escape_time`: Float (Inherited from parent trajectory).

### Regression Result
Output of the deviation analysis.
- **Attributes**:
  - `selected_model`: String (e.g., "power_law", "logarithmic").
  - `noise_level`: $\sigma_{noise}$ (if grouped) or `null` (global).
  - `mean_deviation`: Mean $\Delta \lambda$ across trials.
  - `std_deviation`: Standard error of mean.
  - `regression_coefficients`: Dictionary of model parameters.
  - `p_value`: p-value for the bias term (coefficient of $\sigma_{noise}$).
  - `effect_size`: Cohen's d or similar.
  - `trial_count`: Number of trials used.

## Data Flow

1. **Generation**: `code/simulation/lorenz.py` → `data/raw/trajectories_*.npz`.
2. **Baseline Validation**: `code/analysis/ftle.py` (clean, T=50,000) → `data/processed/baseline.json`.
3. **FTLE Calculation**: `code/analysis/ftle.py` (noisy) → `data/processed/ftle_results.json`.
4. **Regression**: `code/analysis/regression.py` (Model selection + t-test) → `data/processed/regression_results.json`.
5. **Visualization**: `code/analysis/regression.py` → `data/processed/plots/`.

## Storage Format

- **Raw Data**: `numpy` `.npz` (compressed) for trajectories.
- **Processed Data**: `JSON` for structured results (FTLE, regression).
- **Visualizations**: `PNG` (vector-embedded) for plots.

## Checksums

- All files in `data/raw/` and `data/processed/` are checksummed (SHA-256) and recorded in `state/manifest.yaml`.
- No file in `data/` is modified in place. Derivations produce new files.