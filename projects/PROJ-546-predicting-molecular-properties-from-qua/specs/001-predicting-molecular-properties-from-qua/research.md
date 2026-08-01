# Research Question Validation

## Objective
Validate the use of semi-empirical methods (DFTB+) as a proxy for high-level DFT calculations in predicting molecular reaction barriers.

## Hypothesis
Semi-empirical descriptors (HOMO, LUMO, Mayer orders) can predict experimental barriers with accuracy comparable to DFT within a margin of 2.0 kcal/mol, while offering a 10x speedup in computation time.

## Methodology
1. **Data Collection**: Retrieve experimental barrier data from Zenodo.
2. **Descriptor Generation**:
 - Compute DFTB+ descriptors for the full dataset.
 - Compute DFT (B3LYP/def2-SVP) descriptors for a subset.
3. **Modeling**: Train Random Forest models on both descriptor sets.
4. **Evaluation**: Compare MAE against experimental ground truth and perform statistical significance testing.

## Constraints
- Computational budget: ~6 hours for the full pipeline.
- Memory limit: 6.5 GB per process.
- Accuracy threshold: Semi-empirical MAE ≤ 2.0 kcal/mol.