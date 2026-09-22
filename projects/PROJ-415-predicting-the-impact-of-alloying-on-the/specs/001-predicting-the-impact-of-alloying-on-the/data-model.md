# Data Model: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Entities

### DiffusionRecord
Represents a single data point of diffusion in an alloy.
*   `host_element` (str): Symbol of the host metal (e.g., "Ni", "Cu").
*   `solute_element` (str): Symbol of the solute (e.g., "Co", "Zn").
*   `concentration_at_pct` (float): Solute concentration in atomic percent.
*   `activation_energy_eV` (float): Measured activation energy in eV/atom.
*   `crystal_structure` (str): Must be "FCC".
*   `diffusion_mode` (str): Must be "self".
*   `source_id` (str): Identifier for the data source (e.g., "Zenodo-001").
*   `q_host_eV` (float): Activation energy of the pure host metal (0 at.%), retrieved from the dataset or `data/reference/pure_metals_q.csv`.
*   `delta_q_eV` (float): Calculated shift: `activation_energy_eV - q_host_eV`.

### AtomicDescriptor
Computed features for a solute-host pair.
*   `host_radius` (float): Atomic radius of host (pm).
*   `solute_radius` (float): Atomic radius of solute (pm).
*   `size_mismatch` (float): Calculated as `(solute_radius - host_radius) / host_radius`.
*   `electronegativity_diff` (float): Difference in Pauling electronegativity.
*   `valence_electron_diff` (int): Difference in valence electrons.

### ModelArtifact
Output of the training phase.
*   `model_type` (str): "RandomForest", "GradientBoosting", "LinearRegression", "MeanPredictor".
*   `hyperparameters` (dict): JSON dict of tuned parameters.
*   `metrics` (dict): R², RMSE, MAE.
*   `coefficients` (dict): For Linear Regression, includes `size_mismatch`, `p_value`, `ci_lower`, `ci_upper`.

## Data Flow

1.  **Raw Input**: `data/raw/diffusion_raw.csv` (from Zenodo/OpenKIM open subset).
2.  **Filtering**: `data/curated/filtered.csv` (FCC + Self only).
3.  **Baseline Retrieval**: `data/reference/pure_metals_q.csv` (used if dataset lacks 0 at.% rows).
4.  **Enrichment**: `data/curated/enriched.csv` (with AtomicDescriptors and `delta_q_eV`).
5.  **Training**: `models/final_rf.pkl`, `models/final_gb.pkl`, `models/linear_coef.json`.
6.  **Validation**: `results/metrics.json`, `results/sensitivity_analysis.csv`.

## Storage Format

*   **CSV**: UTF-8, comma-delimited, no index.
*   **JSON**: Compact, no pretty-printing for artifacts (except logs).
*   **Pickle**: Protocol 4 (compatible with Python 3.11).

## Constraints

*   `crystal_structure` must be exactly "FCC".
*   `diffusion_mode` must be exactly "self".
*   `activation_energy_eV` must be > 0.
*   `size_mismatch` cannot be NaN.
*   `q_host_eV` must be present for every record to calculate `delta_q_eV`. If not in dataset, must be retrieved from `pure_metals_q.csv`.