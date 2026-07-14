# Scientific Methodology

## Target Variables

The project predicts two key parameters of the Langmuir isotherm:

1. **Langmuir Capacity ($q_{max}$)**: Represents the maximum adsorption capacity of the adsorbent for a specific adsorbate.
2. **Henry Constant ($K_H$)**: Represents the affinity of the adsorbate for the adsorbent at low pressures.

## Molecular Descriptors

The following descriptors are calculated using RDKit to characterize the adsorbate:

- **Molecular Weight (MW)**: Basic size metric.
- **Polar Surface Area (PSA)**: Indicator of polarity and hydrogen bonding capability.
- **Polarizability**: Measure of the ease with which the electron cloud can be distorted; critical for van der Waals interactions.
- **Hydrogen Bond Donors/Acceptors**: Counts of H-bonding sites.
- **Van der Waals Volume**: Steric bulk.
- **Kinetic Diameter**: Effective size of the molecule in motion; crucial for pore accessibility (required for SC-002).

## Consensus List (SC-002)

To validate the scientific relevance of the model, the top-ranked features from SHAP analysis are compared against a literature-derived consensus list of drivers for adsorption:

1. Polarizability
2. Kinetic Diameter
3. Lennard-Jones Energy Parameter
4. Quadrupole Moment
5. Molecular Volume

**Acceptance Criteria**: At least 2 of the top 3 SHAP features must appear in this list when using the external validation dataset.

## Performance Threshold (SC-003)

The model's ability to generalize using only the most critical features is tested:

- **Procedure**: Retrain the best model using only the top 3 descriptors identified by SHAP.
- **Criteria**: The resulting R² on the test set must be $\ge 0.60$.
- **Implication**: If met, it confirms that a small subset of physically meaningful features captures the majority of the variance in adsorption behavior.

## Data Splitting Strategy

To ensure rigorous validation, a **material-level split** is employed:

- **Problem**: Standard random splitting can lead to data leakage if multiple adsorbates are tested on the same adsorbent material.
- **Solution**: Group data by `material_id`. Split the unique materials into train/test sets.
- **Result**: The model is evaluated on its ability to predict adsorption on *unseen materials*, which is the true generalization task.

## Statistical Significance

- **Permutation Testing**: Features are randomly shuffled to establish a null distribution of importance.
- **Benjamini-Hochberg FDR**: Corrects for multiple hypothesis testing when evaluating feature importances, reducing the rate of false positives.
