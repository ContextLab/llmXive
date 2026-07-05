# Data Model: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Entity Definitions

### DiffusionRecord
Represents a single experimental or simulation data point for diffusion in an alloy.
- `id`: Unique identifier (UUID or row index).
- `host_element`: String (e.g., "Ni", "Cu").
- `solute_element`: String (e.g., "Cr", "Mn").
- `crystal_structure`: String (Enum: "FCC", "BCC", "HCP").
- `diffusion_mode`: String (Enum: "self", "solute", "impurity").
- `activation_energy_eV`: Float (Target variable).
- `solute_concentration_at_pct`: Float.
- `solute_radius_pm`: Float (Source: Metallic Radii, Pauling/Wiberg).
- `host_radius_pm`: Float (Source: Metallic Radii, Pauling/Wiberg).
- `source_url`: String (Original dataset reference).

### AtomicDescriptor
Computed features derived from `DiffusionRecord`.
- `size_mismatch`: Float = `(solute_radius - host_radius) / host_radius`.
- `electronegativity_diff`: Float (Pauling scale).
- `valence_electron_diff`: Integer.
- `host_element_one_hot`: List of booleans (One-hot encoding for Host Metal fixed effects).

### ModelArtifact
Output of the training process.
- `model_type`: String ("RandomForest", "GradientBoosting", "LinearRegression").
- `hyperparameters`: Dict (e.g., `{"max_depth": 5, "n_estimators": 100}`).
- `performance_metrics`: Dict (e.g., `{"R2": 0.85, "RMSE": 0.12}`).
- `coefficients`: Dict (Only for Linear Regression, e.g., `{"size_mismatch": 0.45}`).
- `p_values`: Dict (Only for Linear Regression).
- `bootstrap_ci`: Dict (95% CI for coefficients).
- `power_analysis`: Dict (Minimum Detectable Effect, achieved power).
- `sensitivity_analysis`: Dict (Threshold sweep results).

## Data Flow
1.  **Raw Input** (`data/raw/*.csv` or API) -> **Acquisition** (`data/acquisition.py`) -> **Curated** (`data/curated/fcc_self_diffusion.csv`).
2.  **Curated** + **Constants** -> **Features** (`data/curated/features.csv`).
3.  **Features** -> **Model Training** -> **Artifacts** (`models/*.pkl`, `models/*.json`).
4.  **Artifacts** + **Test Set** -> **Validation** -> **Reports** (`reports/validation_report.json`).

## Constraints & Rules
- **No Missing Values**: `solute_concentration` and radii must be present. Rows with missing values are excluded and logged.
- **Unit Consistency**: All energies in eV; all radii in pm (Metallic).
- **FCC Only**: Only records with `crystal_structure == "FCC"` and `diffusion_mode == "self"` are retained for the primary model.
- **Ground Truth**: Target variable $\Delta E_a$ is calculated as $E_{alloy\_measured} - E_{pure\_host\_measured}$, using **experimentally measured** values from the dataset.
- **Descriptor Consistency**: All descriptors must use **Metallic Radii** (Pauling/Wiberg) for FCC coordination.