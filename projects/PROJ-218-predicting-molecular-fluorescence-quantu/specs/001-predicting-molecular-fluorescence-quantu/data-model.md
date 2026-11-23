# Data Model: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

## Overview
All intermediate and final artifacts are described by explicit JSON‑Schema documents. The schemas are validated by contract tests in `tests/contract/`.

## Processed Dataset Schema
The primary dataset produced after cleaning and scaffold splitting is defined by the schema located at:

```
contracts/processed_dataset.schema.yaml
```

Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `smiles` | string | Canonical SMILES string parsed by RDKit. |
| `fqy_raw` | number / null | Experimental fluorescence quantum yield as reported in the source dataset. |
| `fqy_norm` | number / null | Target value after ε‑clipping to the interval (ε, 1‑ε). |
| `scaffold_id` | string | Murcko scaffold identifier used for the scaffold‑based split. |
| `split` | string (`train`, `validation`, `test`) | Indicates the dataset partition. |
| `metadata` | object (optional) | Experimental metadata such as `solvent`, `temperature`, and `measurement_method`. |

The schema ensures that every record contains the required structural and target information, and that any optional metadata conforms to a known structure. All downstream scripts (`src/*`) read and write Parquet files that must validate against this schema.

---



