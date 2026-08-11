# Features Module

This directory contains the descriptor engineering pipeline for solder alloy composition analysis.

## Components

- `transformer.py`: CLR (Centered Log-Ratio) transformation for compositional data
- `descriptor_engine.py`: Computation of physical/chemical descriptors from elemental compositions
- `collinearity.py`: Variance Inflation Factor (VIF) calculation and collinearity detection
- `__init__.py`: Module initialization and public API exports

## Usage

```python
from features import CLRTransformer, DescriptorEngine

# Transform compositional data
transformer = CLRTransformer()
clr_data = transformer.fit_transform(composition_df)

# Compute descriptors
engine = DescriptorEngine()
descriptors = engine.compute_descriptors(composition_df)
```

## Dependencies

- `compositional` library for CLR transformation
- `numpy`, `pandas` for data manipulation
- `statsmodels` for VIF calculation
