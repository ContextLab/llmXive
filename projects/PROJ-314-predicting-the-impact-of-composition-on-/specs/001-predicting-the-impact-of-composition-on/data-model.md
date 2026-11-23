# Data Model: Predicting Weibull Modulus

## Entities

### CeramicEntry

Represents a single ceramic sample with its properties.

**Fields**:
- `composition` (string): Chemical formula (e.g., "Al2O3")
- `weibull_modulus` (float): Weibull modulus value
- `sample_count` (int): Number of samples (N)
- `sintering_temp` (float): Sintering temperature
- `primary_anion_cation_group` (string): Derived group (e.g., "O-Al")
- `is_range_flag` (boolean): True if value was a range
- `range_original` (string): Original range string
- `is_imputed` (boolean): True if value was imputed
- `mean_atomic_radius` (float): Mean atomic radius
- `electronegativity_std` (float): Std dev of electronegativity
- `valence_electron_concentration` (float): VEC

**Validation Rules**:
- `weibull_modulus` must be > 0
- `sample_count` must be >= 30 for valid entries
- `composition` must be parsable by `chemparse`

### DescriptorSet

Represents a set of computed descriptors for a composition.

**Fields**:
- `composition` (string)
- `descriptors` (dict): Mapping of descriptor name to value

## Relationships

- One `CeramicEntry` can have one `DescriptorSet` (1:1)
- `DescriptorSet` is derived from `CeramicEntry.composition`

## Schema Examples

```yaml
# CeramicEntry
composition: "Al2O3"
weibull_modulus: 15.5
sample_count: 50
sintering_temp: 1600.0
primary_anion_cation_group: "O-Al"
is_range_flag: false
range_original: null
is_imputed: false
mean_atomic_radius: 1.2
electronegativity_std: 0.5
valence_electron_concentration: 3.2
```
