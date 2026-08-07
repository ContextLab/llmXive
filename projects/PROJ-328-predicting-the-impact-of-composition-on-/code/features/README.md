# Features Module

This directory contains the descriptor engineering infrastructure for the solder hardness prediction pipeline.

## Components

- `transformer.py`: Implements CLR (Centered Log-Ratio) transformation for compositional data
- `descriptor_engine.py`: Calculates weighted atomic properties and derived descriptors
- `collinearity.py`: Variance Inflation Factor (VIF) calculation and collinearity detection

## Usage

```python
from features.transformer import CLRTransformer
from features.descriptor_engine import DescriptorEngine
from features.collinearity import calculate_vif

# Transform compositional data
transformer = CLRTransformer()
clr_data = transformer.fit_transform(compositional_df)

# Engine descriptors
engine = DescriptorEngine()
descriptors = engine.compute(clr_data, raw_composition_df)

# Check collinearity
vif_scores = calculate_vif(descriptors)
```

## Dependencies

- `compositional`: For CLR transformation
- `numpy`, `pandas`: Data manipulation
- `statsmodels`: VIF calculation
