# Research Idea: Predicting Molecular Properties from Quantum Chemical Calculations

## Motivation
Predicting reaction barrier heights is critical for drug discovery and materials science. High-level DFT is accurate but computationally expensive. Semi-empirical methods (DFTB+) are fast but less accurate. This project aims to bridge the gap by training ML models on semi-empirical descriptors, calibrated against a small set of DFT calculations and experimental data.

## Key Challenges
- **Accuracy vs. Cost**: Balancing the speed of DFTB+ with the accuracy of DFT.
- **Geometry Consistency**: Ensuring identical geometries for fair comparison (Constitution Principle VI).
- **Physical Validity**: Ensuring predictions align with observable structural data (Franklin Review).
- **Approximation Error**: Quantifying the "missing degrees of freedom" in semi-empirical models (Feynman Review).

## Proposed Approach
1. **Data Collection**: Fetch experimental barrier data from Zenodo.
2. **Descriptor Generation**:
 - Run DFTB+ for full dataset (geometry optimization + descriptors).
 - Run Psi4 for subset (using DFTB+ optimized geometries).
3. **Model Training**: Train Random Forests on both descriptor sets.
4. **Evaluation**: Compare MAE against experimental ground truth.
5. **Sensitivity Analysis**: Analyze feature importance and threshold stability.

## Validation Strategy
- **Experimental Ground Truth**: Verify predictions against measured barriers (Curie/Franklin Review).
- **Physical Interpretability**: Trace top features to known chemical invariants (Pauling/Feynman Review).
- **Map vs. Territory**: Distinguish computational artifacts from physical observables (Einstein Review).

## Expected Outcomes
- A pipeline that generates semi-empirical descriptors with < 2.0 kcal/mol MAE.
- Quantitative analysis of approximation errors in DFTB+.
- Identification of robust descriptors that generalize across methods.
