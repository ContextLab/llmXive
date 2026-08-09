# Feature Engineering Module

This directory contains the code for transforming raw solder composition data
into model-ready features.

## Components

1. **transformer.py**: Handles Compositional Data Analysis (CoDA) transformations,
 specifically the Centered Log-Ratio (CLR) transform to address the closure problem.
2. **descriptor_engine.py**: Calculates physical and chemical descriptors (e.g.,
 weighted mean atomic mass, electronegativity variance) based on elemental properties.
3. **collinearity.py**: Computes Variance Inflation Factors (VIF) to detect and
 manage multicollinearity among features.

## Workflow

1. Raw composition data is loaded.
2. `DescriptorEngine` computes raw descriptors.
3. `CLRTransformer` applies the CLR transform to the descriptor vector.
4. `calculate_vif` checks for collinearity before model training.
