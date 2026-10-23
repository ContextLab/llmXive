# Data Model: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
All intermediate and final artifacts are described by explicit schemas. The schemas are validated by the contract tests in `tests/contract/`.

## Processed Dataset Schema (`contracts/processed_dataset.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Processed Molecular Fluorescence Dataset"
type: object
required:
  - smiles
  - fqy_raw
  - fqy_norm
  - scaffold_id
  - split
properties:
  smiles:
    type: string
    description: "Canonical SMILES string parsed by RDKit."
  fqy_raw:
    type: number
    minimum: to be determined
    maximum: a qualitatively high level
    description: "Experimental fluorescence quantum yield as reported (dimensionless)."
  fqy_norm:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Clipped FQY value (Values that would be exactly at the boundaries are clipped to a narrow interior range just above the lower limit and just below the upper limit.); no additional scaling is applied."
  scaffold_id:
    type: string
    description: "Murcko scaffold identifier used for scaffold‑based splitting."
  split:
    type: string
    enum: [train, validation, test]
    description: "Dataset partition."
  metadata:
    type: object
    additionalProperties: true
    description: "Optional fields such as solvent, temperature, measurement method (used as covariates in modeling)."
```

*Only this schema is currently present in the `contracts/` directory, matching the plan’s contract references.*
