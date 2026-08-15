# Data Model: Predicting Weibull Modulus

## Entities

### CeramicEntry

Represents a single ceramic material entry.

**Fields:**
- `composition` (str): Chemical formula (e.g., "Al2O3")
- `weibull_modulus` (float): Target variable
- `sample_count` (int): Number of samples
- `sintering_temp` (float): Sintering temperature
- `primary_anion_cation_group` (str): Derived group identifier

### DescriptorSet

Represents computed features for a composition.

**Fields:**
- `composition` (str)
- `mean_atomic_radius` (float)
- `electronegativity_std` (float)
- `valence_electron_concentration` (float)
- `cation_size_variance` (float)
- `range_uncertainty` (float)
- `is_range_flag` (bool)
- `is_imputed` (bool)

## Relationships

- One `CeramicEntry` corresponds to one `DescriptorSet`.
- `DescriptorSet` is derived from `CeramicEntry` via feature engineering.

## Validation Rules

- `composition` must be a valid chemical formula.
- `weibull_modulus` must be positive.
- `sample_count` must be >= 30 for inclusion.
