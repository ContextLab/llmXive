# Research Question Validation

## Original Question
"Can we predict the elastic moduli of 2D materials from their crystal structure using a GNN?"

## Validation Status
**Status**: Validated with Clarification

## Key Clarification (per Richard Feynman review)
The original project title implied "First-Principles Calculations," which was misleading.
The methodology uses **Structure-Only Surrogate Models** (GNNs) that interpolate existing DFT data,
not solve the Schrödinger equation. This distinction is critical for scientific accuracy.

## Revised Scope
- **Goal**: Build a fast, accurate surrogate model for elastic moduli prediction.
- **Method**: Graph Neural Networks trained on DFT-derived data.
- **Limitation**: Model is interpolative; cannot predict properties for structures far from training distribution.
- **Value**: Rapid screening of 2D materials candidates without expensive DFT runs.

## Next Steps
1. Implement data pipeline to collect high-quality DFT data.
2. Train and validate GNN surrogate.
3. Quantify generalization limits (inter-family drop).
4. Identify key structural descriptors via SHAP/ablation.
