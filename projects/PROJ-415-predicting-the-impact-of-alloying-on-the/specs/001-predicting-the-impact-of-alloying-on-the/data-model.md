# Data Model: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Entity Definitions

### DiffusionRecord
Represents a single experimental or simulation data point.
- `id`: Unique identifier (string)
- `host_element`: Chemical symbol (e.g., "Ni", "Cu") (string)
- `solute_element`: Chemical symbol (e.g., "Co", "Fe") (string)
- `crystal_structure`: Crystal lattice type (e.g., "FCC", "BCC", "HCP") (string)
- `diffusion_mode`: Diffusion mechanism (e.g., "self", "solute") (string)
- `activation_energy_eV`: Activation energy in electron-volts (float)
- `solute_concentration_at_pct`: Concentration in atomic percent (float)
- `source_url`: URL of the original data source (string)

### AtomicDescriptor
Derived features for a specific solute-host pair.
- `host_radius_angstrom`: Atomic radius of host (float)
- `solute_radius_angstrom`: Atomic radius of solute (float)
- `size_mismatch`: Normalized radius difference (float)
- `electronegativity_diff`: Difference in Pauling electronegativity (float)
- `valence_electron_count`: Valence electrons of solute (int)

### BaselineShift
Represents the calculated shift in activation energy relative to the pure host.
- `solute_element`: Chemical symbol of the solute (string)
- `host_element`: Chemical symbol of the host (string)
- `predicted_energy_eV`: Predicted activation energy (float)
- `pure_host_energy_eV`: Activation energy of the pure host (float)
- `baseline_shift_eV`: Difference (predicted - pure) (float)

### ModelArtifact
Trained model metadata.
- `model_type`: "RandomForest", "GradientBoosting", "LinearRegression" (string)
- `hyperparameters`: JSON object of parameters (object)
- `metrics`: JSON object of R², RMSE, MAE (object)
- `coefficients`: JSON object of model coefficients (if applicable) (object)
- `p_values`: JSON object of p-values (if applicable) (object)

## Data Flow

1.  **Ingestion**: Raw CSV/Parquet → `data/raw/`
2.  **Curation**: `data/raw/` → Filter (FCC primary, HCP fallback) → `data/curated/filtered.csv`
3.  **Feature Engineering**: `filtered.csv` + Periodic Table → `data/curated/features.csv`
4.  **Baseline Calculation**: `filtered.csv` → `code/validation/baseline.py` → `data/curated/baseline_shifts.csv` (FR-008)
5.  **Training**: `features.csv` → Split (Train/Test) → Model Artifacts (`models/`)
6.  **Validation**: Model + Test Set → `reports/validation_report.json`

## Assumptions & Constraints

-   **Atomic Data**: All atomic properties are derived from the `periodictable` library (version pinned).
-   **Missing Data**: Rows with missing atomic radii are excluded and logged.
-   **Unit Standardization**: All activation energies must be in eV. All concentrations in at.%.
-   **No Synthetic Data**: The `data/curated/` directory must not contain generated rows unless explicitly marked as "synthetic" (which is forbidden by FR-001).
-   **Pivot Logic**: If FCC data is unavailable, the flow automatically switches to HCP data without altering the schema.
