# Data Model: Predicting the Impact of Alloying on the Diffusion Activation Energy in FCC Metals

## Entity Definitions

### DiffusionRecord
| Field | Type | Description |
|-------|------|-------------|
| `host_element` | string | Chemical symbol of the host metal (e.g., "Ni"). |
| `solute_element` | string | Chemical symbol of the solute element (e.g., "Cu"). |
| `crystal_structure` | string (enum) | Must be `"FCC"`. |
| `diffusion_mode` | string (enum) | `"self"` for baseline, `"solute"` or `"impurity"` for training. |
| `concentration_at_percent` | number | Solute concentration in atomic %. Retained as a covariate in the inferential model. |
| `activation_energy_eV` | number | Measured activation energy in eV. |
| `source_id` | string | Identifier of the original NIST SRD 150 entry. |

### AtomicDescriptor
| Field | Type | Description |
|-------|------|-------------|
| `host_radius` | number | Atomic radius of host (pm). |
| `solute_radius` | number | Atomic radius of solute (pm). |
| `size_mismatch` | number | `(solute_radius - host_radius) / host_radius`. |
| `electronegativity_diff` | number | `|χ_solute - χ_host|` (Pauling scale). |
| `valence_electron_diff` | integer | Difference in valence electron count. |

### ModelArtifact
| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string (enum) | `"RandomForest"`, `"GradientBoosting"` or `"LinearRegression"`. |
| `hyperparameters` | object | Tuned hyper-parameters (e.g., `max_depth`, `n_estimators`). |
| `metrics` | object | `r_squared`, `rmse`, `mae`. |
| `coefficients` | object | Present only for Linear Regression (size mismatch coefficient, intercept, etc.). |
| `timestamp` | string (ISO 8601) | Creation time. |
| `seed` | integer | Random seed used for training. |

## File Schemas

### Input: `data/raw/nist_diffusion_raw.csv`
*Source*: NIST SRD 150 (or a verified mirror).  
*Format*: CSV with columns matching **DiffusionRecord** plus any additional raw fields.

### Output: `data/curated/baselines.csv`
*Filter*: `crystal_structure == "FCC"` **and** `diffusion_mode == "self"` (per current FR-001).  
*Columns*: `host_element`, `activation_energy_eV` (pure-host baseline \(Q_{\text{host}}\)).

### Output: `data/curated/filtered.csv` (Single Source of Truth)
*Conformance*: This file MUST validate against `contracts/dataset.schema.yaml`.  
*Filter*: `crystal_structure == "FCC"`; `diffusion_mode` per FR-001 (self-only under the current spec; solute/impurity rows pending the flagged FR-001 spec amendment).  
*Columns*:
- `host_element`
- `solute_element`
- `concentration_at_percent` (covariate in the inferential model)
- `activation_energy_eV`
- `size_mismatch`
- `electronegativity_diff`
- `valence_electron_diff`
- `baseline_shift_eV` (`activation_energy_eV - Q_host`)

### Output: `models/final_rf.pkl`, `models/final_gb.pkl`
*Format*: Pickle containing the trained scikit-learn model.

### Output: `models/linear_coef.json`
*Conformance*: This file MUST validate against `contracts/model_output.schema.yaml` (fields: `model_type`, `coefficients`, `statistics`, `metrics`).  
*Format*: JSON with the multivariate linear model's coefficients (including `size_mismatch` and intercept), standard error, bootstrap p-value (percentile-inversion procedure, 10,000 resamples), and 95 % bootstrap CI.

### Output: `validation/stability_index_report.json`
*Format*: JSON adhering to `validation_report.schema.yaml` (threshold sweep data + stability index).

## Data Flow Diagram
```mermaid
graph TD
    A[NIST Raw Data] -->|streaming_loader| B{Data Availability Check}
    B -- Fail --> C[HALT: No Data]
    B -- Pass --> D[Filter: FCC self-diffusion per FR-001]
    D --> E[Baseline Set (self)]
    E --> F[Extract Q_host per host]
    F --> G[Feature Engineering (size mismatch, etc.)]
    G --> H[Merge baseline_shift]
    H --> I[Train RF & GB]
    H --> J[Train Linear Regression]
    I --> K[Performance Metrics]
    J --> L[Bootstrap Significance]
    L --> M[Sensitivity Analysis]
    M --> N[Stability Index Report]
```

## Assumptions & Constraints
- Atomic radii and electronegativities are taken from the **pinned** `periodictable==0.20.1` library (Principle VII).  
- All activation energies are in **eV**; concentrations are in **at %**.  
- No personally identifying information is present in the diffusion dataset (Principle III).  