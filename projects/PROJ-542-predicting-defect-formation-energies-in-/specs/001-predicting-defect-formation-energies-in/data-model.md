# Data Model: Predicting Defect Formation Energies in Perovskites with Machine Learning

## Overview
The project manipulates seven primary data artefacts (the feature matrix may be overwritten with additional structural descriptors during the fallback phase):

| Artefact | Description | Location | Format |
|----------|-------------|----------|--------|
| **Raw defect dataset** | Original perovskite compositions with DFT oxygen‑vacancy formation energies (and optional metadata, including optional structure CIF/POSCAR, DFT functional, temperature, pressure). | `data/raw/materials_defects.csv` | CSV |
| **Engineered feature matrix** | Twelve compositional descriptors (atomic radius, Pauling electronegativity, oxidation state, valence electron count for A, B, X) **plus** the target energy. May be replaced by an augmented matrix containing structural descriptors on fallback. | `data/processed/features.csv` (or `features_augmented.csv`) | CSV |
| **Cross‑validation metrics** | Summary statistics (mean ± std) for each model across CV folds. | `data/processed/cv_metrics.json` | JSON |
| **Model performance report** | JSON containing CV metrics, held‑out test metrics, bootstrap CI, paired t‑test result, and ranked feature importances. | `data/processed/performance.json` | JSON |
| **Final figures** | Scatter plot of predictions vs. actual energies and bar chart of feature importances. | `figures/` (PNG files) | PNG |
| **Checksums** | SHA‑256 checksums for raw and derived files to ensure data hygiene. | `data/checksums/` | TXT |
| **Runtime log** | Total wall‑clock time and any budget‑exceed warnings. | `runtime.log` | TXT |
| **Metadata (confounders)** | Extracted DFT functional, calculation settings, temperature, pressure (if present) from the Materials Project response. | `data/raw/metadata.json` | JSON |

## Schema Definitions

### `contracts/raw_dataset.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Raw Defect Dataset"
type: object
required:
  - composition
  - defect_type
  - formation_energy
properties:
  composition:
    type: string
    description: "Perovskite formula in standard notation (e.g., 'BaTiO3')."
  defect_type:
    type: string
    enum: ["oxygen_vacancy"]
    description: "Type of defect; only 'oxygen_vacancy' is supported."
  formation_energy:
    type: number
    description: "DFT‑computed defect formation energy in eV."
  metadata:
    type: object
    description: "Optional additional fields (e.g., Materials Project ID, DFT functional, temperature, pressure)."
  structure_cif:
    type: string
    description: "Optional path or URL to a CIF/POSCAR file containing the crystal structure."
additionalProperties: false
```

### `contracts/features.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Engineered Feature Matrix"
type: object
required:
  - A_radius
  - A_electronegativity
  - A_oxidation_state
  - A_valence_electrons
  - B_radius
  - B_electronegativity
  - B_oxidation_state
  - B_valence_electrons
  - X_radius
  - X_electronegativity
  - X_oxidation_state
  - X_valence_electrons
  - formation_energy
properties:
  A_radius:
    type: number
  A_electronegativity:
    type: number
  A_oxidation_state:
    type: integer
  A_valence_electrons:
    type: integer
  B_radius:
    type: number
  B_electronegativity:
    type: number
  B_oxidation_state:
    type: integer
  B_valence_electrons:
    type: integer
  X_radius:
    type: number
  X_electronegativity:
    type: number
  X_oxidation_state:
    type: integer
  X_valence_electrons:
    type: integer
  formation_energy:
    type: number
  # Optional structural descriptors added on fallback.
  coordination_number:
    type: number
    description: "Average coordination number of the B‑site (added on fallback)."
  average_bond_length:
    type: number
    description: "Mean bond length in Å (added on fallback)."
  crystal_symmetry:
    type: string
    description: "Crystal symmetry label (e.g., 'cubic', added on fallback)."
additionalProperties: false
```

### `contracts/model_performance.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Performance Report"
type: object
required:
  - cv_metrics
  - test_metrics
  - bootstrap_ci
  - paired_ttest
  - feature_importances
properties:
  cv_metrics:
    type: object
    description: "Cross‑validation summary for each model."
    patternProperties:
      "^(RandomForest|GradientBoosting)$":
        type: object
        required:
          - rmse_mean
          - rmse_std
          - mae_mean
          - mae_std
          - r2_mean
          - r2_std
        properties:
          rmse_mean:
            type: number
          rmse_std:
            type: number
          mae_mean:
            type: number
          mae_std:
            type: number
          r2_mean:
            type: number
          r2_std:
            type: number
  test_metrics:
    type: object
    required:
      - model_name
      - rmse
      - mae
      - r2
    properties:
      model_name:
        type: string
      rmse:
        type: number
      mae:
        type: number
      r2:
        type: number
  bootstrap_ci:
    type: object
    required:
      - rmse_lower
      - rmse_upper
      - confidence
    properties:
      rmse_lower:
        type: number
      rmse_upper:
        type: number
      confidence:
        type: number
        description: "Confidence level (e.g., 0.95)."
  paired_ttest:
    type: object
    required:
      - t_statistic
      - p_value
      - alpha
    properties:
      t_statistic:
        type: number
      p_value:
        type: number
      alpha:
        type: number
        description: "Significance threshold (0.05)."
  feature_importances:
    type: array
    description: "Sorted list of descriptor importance objects."
    items:
      type: object
      required:
        - feature
        - importance
      properties:
        feature:
          type: string
          description: "Descriptor name (e.g., 'A_radius')."
        importance:
          type: number
          description: "Relative importance (normalized to sum = 1)."
additionalProperties: false
```

## Data Flow Diagram (textual)
```
raw CSV (or API fetch) → checksum → raw_dataset.schema.yaml validation
raw CSV → metadata extraction (metadata.json) → confounder log
raw CSV → featurize.py (pymatgen) → features.csv → features.schema.yaml validation
features.csv → validate.py (size & completeness, ≥ 500 rows for primary analysis; ≥ 50 rows for CV) → validation.log
features.csv → split.py → train.csv / test.csv / validation.csv
train.csv → train.py (GroupKFold) → cv_metrics.json + model pickles
train.csv + test.csv → evaluate.py → performance.json + figures
if performance fails → fallback.py (adds structural descriptors, uses validation.csv) → repeat train/evaluate
confounder_integration.py (optional) merges selected metadata fields into training matrices before training/evaluation.
pipeline.ipynb orchestrates all steps, writes checksums after each artefact, and runs contract validation.
```

## Contract‑Artifact Mapping (for traceability)
| Artifact | Contract |
|----------|----------|
| `data/raw/materials_defects.csv` | `contracts/raw_dataset.schema.yaml` |
| `data/raw/metadata.json` | (internal confounder log; no external schema) |
| `data/processed/features.csv` (or `features_augmented.csv`) | `contracts/features.schema.yaml` |
| `data/processed/cv_metrics.json` | `contracts/model_performance.schema.yaml` (partial) |
| `data/processed/performance.json` | `contracts/model_performance.schema.yaml` (full) |
| `models/*.pkl` | Implicitly referenced by `model_performance.schema.yaml` (model files are ancillary) |
| `figures/*.png` | Visual artefacts referenced in the performance report (no schema needed) |
| `data/checksums/*.sha256` | Internal integrity manifest (validated by CI, not by external schema) |

---


