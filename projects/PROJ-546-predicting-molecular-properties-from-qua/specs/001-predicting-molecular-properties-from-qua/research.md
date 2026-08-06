# Research: Predicting Molecular Properties from Quantum Chemical Calculations

## Dataset Strategy

| Dataset Name | URL                                                              | Variables Used | Purpose             |
|--------------|-------------------------------------------------------------------|----------------|---------------------|
| Experimental Barrier | [https://huggingface.co/datasets/matchbench/semi-homo/resolve/main/test.csv](https://huggingface.co/datasets/matchbench/semi-homo/resolve/main/test.csv) | `smiles`, `experimental_barrier`, `molecule_id` | Training & Evaluation |

## Computational Methods

### Semi-Empirical Calculations (DFTB+)

*   **Software**: DFTB+ v2.2
*   **Method**: Geometry optimization using DFTB+ with default parameters.
*   **Rationale**: DFTB+ offers a computationally efficient approach for generating initial geometries and descriptors for the entire dataset.

### High-Level DFT Calculations (Psi4)

*   **Software**: Psi4 v0.16
*   **Method**: Single-point energy calculations using B3LYP/def2-SVP basis set on optimized geometries from DFTB+.
*   **Rationale**: Provides a more accurate baseline for comparison with experimental data, albeit at higher computational cost. A stratified subset of 50 samples will be used to manage resources.

### Machine Learning Models

*   **Algorithm**: Random Forest Regression
*   **Library**: Scikit-learn
*   **Rationale**: Robust and interpretable algorithm suitable for regression tasks with moderate complexity. Two models will be trained for comparative analysis.

## Decision/Rationale: CPU vs GPU

All calculations (DFTB+, Psi4, model training) will primarily run on the CPU due to resource constraints of the GitHub Actions runner. The model is small enough for efficient computation on a 2-core CPU with limited RAM. No explicit GPU acceleration is planned. If larger datasets or more complex models are needed in future iterations, scaling to Kaggle GPUs (as an escape hatch) will be considered.

## Potential Concerns & Mitigation Strategies

*   **Convergence Failures**: Implement error handling and logging mechanisms to skip molecules that fail to converge during DFTB+ optimization.
*   **Out-of-Memory Errors**: Monitor memory usage and potentially reduce the size of the dataset or use streaming techniques if necessary.
*   **Physical Invalidity (HOMO >= LUMO)**: Skip invalid molecules and log them for further investigation.
