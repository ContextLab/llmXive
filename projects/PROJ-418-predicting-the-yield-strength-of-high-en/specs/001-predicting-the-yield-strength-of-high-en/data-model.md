# Data Model: Predicting the Yield Strength of High-Entropy Alloys via Compositional Descriptors

## Overview

This document defines the schema for the input data, derived descriptors, and output metrics. It ensures data integrity and type safety throughout the pipeline.

## Input Data Schemas

### 1. Elemental Properties (Reference)
Source: `WebElements` (Verified URL: `)

| Field | Type | Description |
|:--- |:--- |:--- |
| `element_symbol` | string | Element symbol (e.g., "Fe", "Cr") |
| `atomic_radius` | float | Atomic radius in pm |
| `electronegativity` | float | Pauling electronegativity |
| `valence_electrons` | integer | Number of valence electrons |
| `melting_point` | float | Melting point in Kelvin |

### 2. HEA Composition (Target)
Source: **Verified HEA Dataset** (URL to be determined from "Verified datasets" block)

| Field | Type | Description |
|:--- |:--- |:--- |
| `alloy_id` | string | Unique identifier for the alloy |
| `elements` | string | JSON string of elemental fractions (e.g., `{"Fe": 0.3, "Cr": 0.2,...}`) |
| `phase` | string | Phase structure (e.g., "FCC", "BCC", "Single-phase") |
| `testing_temp` | float | Testing temperature in Celsius |
| `yield_strength` | float | Yield strength in MPa |
| `source` | string | Original data source (e.g., "Zenodo-12345") |

## Derived Data Schemas

### 3. Processed Dataset (Post-Descriptor Calculation)
Source: `data/processed/hea_descriptors.csv`

| Field | Type | Description |
|:--- |:--- |:--- |
| `alloy_id` | string | Unique identifier |
| `delta` | float | Atomic size mismatch (δ) |
| `delta_chi` | float | Electronegativity variance (Δχ) |
| `vec` | float | Valence electron concentration (VEC) |
| `mixing_entropy` | float | Configurational mixing entropy (R) |
| `melting_var` | float | Melting temperature variance |
| `yield_strength` | float | Target variable (MPa) |
| `is_single_phase` | boolean | Filter flag (True if single-phase) |
| `is_room_temp` | boolean | Filter flag (True if 20-25°C) |

## Output Schemas

### 4. Metrics Report
Source: `output/metrics.json`

```yaml
type: object
properties:
 linear_regression:
 type: object
 properties:
 R2: { type: number }
 MAE: { type: number }
 RMSE: { type: number }
 VIF:
 type: object
 additionalProperties: { type: number }
 random_forest:
 type: object
 properties:
 R2: { type: number }
 MAE: { type: number }
 RMSE: { type: number }
 permutation_p_values:
 type: object
 additionalProperties: { type: number }
 gradient_boosting:
 type: object
 properties:
 R2: { type: number }
 MAE: { type: number }
 RMSE: { type: number }
 permutation_p_values:
 type: object
 additionalProperties: { type: number }
 bootstrap:
 type: object
 properties:
 R2_ci_95:
 type: array
 items: { type: number }
 minItems: 2
 maxItems: 2
 sensitivity:
 type: array
 items:
 type: object
 properties:
 alpha: { type: number }
 significant_count: { type: integer }
 R2: { type: number }
 data_status:
 type: object
 properties:
 N_total: { type: integer }
 N_single_phase: { type: integer }
 N_room_temp: { type: integer }
 power_flag: { type: string, enum: ["OK", "Insufficient Power"] }
```