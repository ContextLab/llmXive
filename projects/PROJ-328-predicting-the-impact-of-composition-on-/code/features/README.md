# Feature Engineering Module

This directory contains the logic for transforming raw solder compositions into machine learning-ready descriptors.

## Components

- `transformer.py`: Implements the Centered Log-Ratio (CLR) transform to handle the compositional nature of the data (closure problem).
- `descriptor_engine.py`: Calculates physical property descriptors (atomic mass, electronegativity, etc.) weighted by composition.
- `collinearity.py`: Calculates Variance Inflation Factors (VIF) to detect and handle multicollinearity among features.

## Usage

These modules are typically invoked by `descriptor_engine_main.py` or integrated into the model training pipeline.
