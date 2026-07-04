# Data Model: Exploring the Correlation Between Molecular Flexibility and Drug Transport Across Cell Membranes

## Entities

### Molecule
- **SMILES**: string (canonicalized)  
- **Molecular Weight (MW)**: float (g/mol)  
- **logP**: float (octanol-water partition coefficient)  
- **PSA**: float (polar surface area, Å²)  
- **logPapp**: float (Caco-2 permeability, cm/s)  
- **Assay Protocol**: string (standard_type)  
- **Conformer Ensemble**: list of 3D coordinates (20 conformers)  
- **Flexibility Descriptors**: dict (bond_variance, angle_variance, dihedral_variance)  

### FlexibilityDescriptor
- **bond_variance**: float (Å²)  
- **angle_variance**: float (rad²)  
- **dihedral_variance**: float (rad²)  
- **ensemble_size**: int (20)  
- **energy_window**: float (10 kcal/mol)  

### CorrelationResult
- **descriptor_type**: string (bond/angle/dihedral)  
- **method**: string (Pearson/Spearman)  
- **r**: float (correlation coefficient)  
- **p_value**: float  
- **q_value**: float (FDR-corrected)  
- **ci_lower**: float (95% CI lower)  
- **ci_upper**: float (95% CI upper)  
- **associational_only**: boolean (flag indicating results are associational)  

### ModelPerformance
- **mean_r2**: float  
- **mean_rmse**: float  
- **mean_mae**: float  
- **fold_r2**: list of 5 floats  
- **confounder_coefficients**: dict (logP, MW, PSA, flexibility_descriptor)  

## Data Flow

1. **Raw Data**: ChEMBL API → `data/raw/chembl_caco2_raw.csv`  
2. **Validated Data**: Filtered SMILES/logPapp → `data/processed/validated_molecules.csv`  
3. **Conformers**: 3D ensembles → `data/processed/conformers.parquet`  
4. **Descriptors**: Flexibility metrics → `data/processed/flexibility_descriptors.csv`  
5. **Results**: Correlation/model outputs → `data/processed/results.json`  

## Transformations

- **Validation**: Remove NULL SMILES/logPapp; filter `standard_type=MEASUREMENT`.  
- **Conformer Generation**: RDKit `EmbedMultipleConfs` with 20 conformers, MMFF94 optimization.  
- **Descriptor Computation**: Variance of internal coordinates across ensemble.  
- **Correlation**: Pearson/Spearman with FDR correction.  
- **Model**: Linear regression with scaffold-based 5-fold CV and VIF/Ridge fallback.  

## Assumptions

- SMILES strings are canonical and valid for RDKit parsing.  
- logPapp values are in consistent units (cm/s).  
- Conformer ensembles adequately represent conformational space (20 samples).  
- Bond and angle variances are near-zero and are included for completeness but are not primary predictors.  
- Dihedral variance is the primary flexibility metric.  
- Scaffold-based splitting prevents data leakage in cross-validation.  
- VIF diagnosis and Ridge regression fallback handle collinearity.  
- Convergence check ensures 20 conformers yield stable variance estimates.
