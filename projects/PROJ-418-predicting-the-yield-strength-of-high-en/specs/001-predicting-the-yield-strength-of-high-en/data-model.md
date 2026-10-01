# Data Model: Predicting the Yield Strength of High‑Entropy Alloys

## Overview
The pipeline works with a small set of well‑defined JSON/YAML schemas that capture raw inputs, derived descriptors, model artifacts, and reporting metadata. All schemas are version‑controlled under `contracts/` and validated with `jsonschema`.

## Schemas

### 1. `contracts/dataset.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Dataset Schema"
type: object
required:
  - alloy_id
  - composition
  - yield_strength
properties:
  alloy_id:
    type: string
    description: "Unique identifier for the alloy."
  composition:
    type: object
    description: "Elemental fractions; keys are element symbols, values sum to 1."
    additionalProperties:
      type: number
      minimum: 0
      maximum: 1
  yield_strength:
    type: number
    description: "Measured yield strength in MPa."
```

### 2. `contracts/descriptor.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "HEA Descriptor Table"
description: "Row‑wise deterministic descriptors for each alloy composition."
type: object
properties:
  composition:
    type: string
    description: "Alloy composition formula (e.g., 'CoCrFeMnNi')."
  mixing_entropy:
    type: number
    description: "Configurational mixing entropy (J mol⁻¹ K⁻¹)."
  atomic_size_mismatch:
    type: number
    description: "δ, atomic size mismatch (dimensionless)."
  electronegativity_variance:
    type: number
    description: "Δχ, variance of Pauling electronegativities."
  vec:
    type: number
    description: "Valence electron concentration (electrons per atom)."
  tm_variance:
    type: number
    description: "Variance of melting temperatures of constituent elements."
required:
  - composition
  - mixing_entropy
  - atomic_size_mismatch
  - electronegativity_variance
  - vec
  - tm_variance
additionalProperties: false
```

### 3. `contracts/elemental_properties.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Elemental Properties Schema"
type: object
required:
  - element
  - atomic_radius
  - electronegativity
  - valence_electrons
  - melting_point
properties:
  element:
    type: string
    description: "Chemical symbol (e.g., Fe, Ni)."
  atomic_radius:
    type: number
    description: "Atomic radius (pm)."
  electronegativity:
    type: number
    description: "Pauling electronegativity."
  valence_electrons:
    type: integer
    description: "Number of valence electrons."
  melting_point:
    type: number
    description: "Melting temperature (K)."
```

### 4. `contracts/metrics.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Model Performance Metrics"
type: object
required:
  - r2
  - pearson_r
  - p_value
  - r2_ci
  - pearson_r_ci
properties:
  r2:
    type: number
    description: "Coefficient of determination on the test set."
  pearson_r:
    type: number
    description: "Pearson correlation coefficient on the test set."
  p_value:
    type: number
    description: "Two‑tailed p‑value for Pearson r."
  r2_ci:
    type: array
    items:
      type: number
    minItems: 2
    maxItems: 2
    description: "95 % bootstrap confidence interval for R²."
  pearson_r_ci:
    type: array
    items:
      type: number
    minItems: 2
    maxItems: 2
    description: "95 % bootstrap confidence interval for Pearson r."
```

### 5. `contracts/importance.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Permutation Importance Results"
type: object
required:
  - feature
  - importance_score
  - raw_p_value
  - holm_bonferroni_p
properties:
  feature:
    type: string
    description: "Descriptor name."
  importance_score:
    type: number
    description: "Mean decrease in score across permutations."
  raw_p_value:
    type: number
    description: "Permutation test p‑value before correction."
  holm_bonferroni_p:
    type: number
    description: "Holm‑Bonferroni corrected p‑value."
```

### 6. `contracts/manifest.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Provenance Manifest"
type: object
required:
  - run_id
  - timestamp
  - seeds
  - package_versions
  - checksums
properties:
  run_id:
    type: string
    description: "UUID for the pipeline execution."
  timestamp:
    type: string
    format: date-time
    description: "ISO‑8601 timestamp of run start."
  seeds:
    type: object
    description: "All random seeds used."
    additionalProperties:
      type: integer
  package_versions:
    type: object
    description: "Pinned versions of every Python package."
    additionalProperties:
      type: string
  checksums:
    type: object
    description: "SHA256 checksums of all input and derived files."
    additionalProperties:
      type: string
```

All schemas are stored under `contracts/` and referenced by the CI validation steps.
