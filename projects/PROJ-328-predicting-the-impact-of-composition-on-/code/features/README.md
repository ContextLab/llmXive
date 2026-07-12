# Feature Engineering Module

This directory contains the code for transforming raw solder alloy compositions
into predictive descriptors and managing feature engineering pipelines.

## Components

### Transformer (`transformer.py`)
- `CLRTransformer`: Implements the Centered Log-Ratio (CLR) transformation
 to handle the compositional nature of alloy data (closure problem).

### Descriptor Engine (`descriptor_engine.py`)
- `DescriptorEngine`: Calculates physical and chemical descriptors from
 CLR-transformed compositions, including:
 - Weighted mean atomic mass
 - Electronegativity variance
 - Atomic radius variance
 - Weighted average melting point
 - Valence electron concentration

### Collinearity (`collinearity.py`)
- `calculate_vif`: Computes Variance Inflation Factors to detect
 multicollinearity among engineered features.

## Usage

```python
from features import CLRTransformer, DescriptorEngine

# Transform compositions
transformer = CLRTransformer()
clr_data = transformer.transform(raw_compositions)

# Engineer descriptors
engine = DescriptorEngine()
descriptors = engine.compute(clr_data, elemental_properties)
```

## Dependencies

- `compositional`: For CLR transformation
- `numpy`, `pandas`: Data manipulation
- `statsmodels`: VIF calculation
