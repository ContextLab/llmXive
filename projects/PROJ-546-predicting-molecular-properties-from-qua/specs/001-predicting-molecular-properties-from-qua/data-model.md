# Data Model: Predicting Molecular Properties from Quantum Chemical Calculations

## Input Data

The primary input is a CSV file containing experimental barrier data, as specified in the project spec. The dataset includes SMILES strings representing molecular structures, their corresponding experimental barriers (in kcal/mol), and unique molecule identifiers.

*   **File Format**: CSV
*   **Columns**:
    *   `smiles`: String representing the molecular structure in SMILES format.
    *   `experimental_barrier`: Float representing the barrier height in kcal/mol.
    *   `molecule_id`: Unique identifier for each molecule.

## Descriptors

The following descriptors will be computed using DFTB+ and Psi4:

*   **HOMO energy**: Float, Highest Occupied Molecular Orbital energy (eV).
*   **LUMO energy**: Float, Lowest Unoccupied Molecular Orbital energy (eV).
*   **Mayer bond order**: Float, Mayer bond order for each bond in the molecule (dimensionless).  Averaged across all bonds to create a single descriptor.

## Output Data

The following output data will be generated during the pipeline:

*   `data/descriptors_semi.csv`: CSV file containing SMILES strings and computed semi-empirical descriptors (HOMO, LUMO, Mayer bond order) for each molecule in the dataset.
*   `data/descriptors_dft.csv`: CSV file containing SMILES strings and computed DFT descriptors (HOMO, LUMO, Mayer bond order) for the stratified subset of 50 molecules.
*   `reports/evaluation.json`: JSON file containing model evaluation metrics (MAE) for both Random Forest models trained on DFT descriptors. It will also include the p-value from a paired t-test comparing their performance.
*   `reports/sensitivity.csv`: CSV file listing top descriptors and cumulative importance based on feature importance analysis.
