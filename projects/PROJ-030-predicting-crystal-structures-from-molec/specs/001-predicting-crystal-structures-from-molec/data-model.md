# Data Model

## Entities

### MoleculeRecord
- `smiles`: str (Canonical SMILES)
- `space_group`: str (International Tables number or symbol)
- `lattice_params`: Dict[str, float] (a, b, c, alpha, beta, gamma)
- `fingerprint`: List[int] (ECFP4 bits)
- `molecular_weight`: float
- `source_id`: str (COD ID)

### ModelMetrics
- `model_type`: str
- `accuracy`: float
- `macro_f1`: float
- `r_squared`: float (for regression)
- `mae`: float
- `baseline_comparison`: Dict[str, float]

### FeatureImportance
- `bit_index`: int
- `importance_score`: float
- `substructure_smiles`: Optional[str]
- `collision_flag`: bool
