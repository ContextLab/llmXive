# Data Model: Predicting Molecular Halide Binding Affinities

## Overview
The data model defines the schema for all intermediate and final artifacts produced by the pipeline. Each artifact is validated against a JSON Schema located in `contracts/`.

## Entity Definitions

### 1. HostMolecule
| Attribute | Type | Description |
|-----------|------|-------------|
| `host_id` | string | Unique identifier (e.g., `HOST_001`). |
| `smiles` | string | Canonical SMILES string (RDKit‑parsable). |
| `inchi` | string (optional) | InChI representation. |
| `source` | string (`"NIST"`, `"PubChem"`, `"Simulated"`) | Origin of the record. |

### 2. BindingMeasurement
| Attribute | Type | Description |
|-----------|------|-------------|
| `measurement_id` | string | Unique identifier. |
| `host_id` | string | FK to `HostMolecule`. |
| `halide_identity` | string (`"F-"`, `"Cl-"`, `"Br-"`, `"I-"`) | Halide ion. |
| `binding_constant` | number | Log K or ΔG (simulated if needed). |
| `solvent` | string (`"acetonitrile"`, `"chloroform"`, `"dichloromethane"`) | Solvent used. |
| `reference_doi` | string | DOI of source or `"SIMULATED"`. |

### 3. ModelRun
| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | string | Unique identifier for the model‑run. |
| `model_type` | string (`"random_forest"` or `"gradient_boosting"`) | Algorithm used. |
| `data_mode` | string (`"Real"` or `"Simulated"`) | Data provenance. |
| `metrics` | object | `{r2_mean, r2_std, rmse_mean, rmse_std}` (see `contracts/model_output.schema.yaml`). |
| `fold_metrics` | list of objects | Each object: `{fold:int, r2:number, rmse:number}`. |
| `feature_stability` | list of objects | `{feature_name:string, cv:number, is_stable:boolean}`. |

## Data Flow & File Layout
- **CSV Implementation**: The pipeline writes a **single wide‑format CSV** (`halide_binding_data.csv`) where **each row corresponds to a single measurement** and **contains both host‑level fields** (`host_id`, `smiles`, `charge_density`, `cavity_volume`, `source`) **and measurement‑level fields** (`halide_identity`, `binding_constant`, `solvent`). This CSV directly implements the combined entity described by `HostMolecule` + `BindingMeasurement` and conforms to `contracts/dataset.schema.yaml`.  
- In Simulated mode, each host row carries exactly one halide measurement (single‑halide mode per the applicable functional requirement).  
- The logical separation into `HostMolecule` and `BindingMeasurement` is retained in documentation for clarity and future extensibility; **no separate physical files are produced** for these entities.  

## Data Files
1. `data/processed/halide_binding_data.csv` – validated against `dataset.schema.yaml`.  
2. `data/processed/independent_eval.csv` – independent evaluation set, also validated against `dataset.schema.yaml`.  
3. `data/processed/model_runs.json` – list of `ModelRun` objects, validated against `model_output.schema.yaml`.  
4. `data/processed/feature_analysis.json` – feature‑stability results.  
5. `data/processed/report.md` – final narrative report (structure checked against `output.schema.yaml`).  

---
