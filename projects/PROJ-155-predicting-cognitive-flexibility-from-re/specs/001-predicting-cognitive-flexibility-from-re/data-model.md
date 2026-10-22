# Data Model: Predicting Cognitive Flexibility from Resting‑State Functional Connectivity Variability

## Overview
The data model defines the schema of every persisted artifact produced by the pipeline. All tabular outputs must conform to the JSON‑Schema contracts in `contracts/`.

## Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **Subject** | Demographic and quality‑control metadata for each participant. | `Subject_ID` (PK), `Age`, `Sex`, `Mean_FD`, `Total_Scan_Time`, `Flexibility_Score`, `Status` |
| **RSFC_Variability** | Principal components derived from edge‑wise dynamic connectivity metrics, plus null‑model p‑value and motion‑noise residual. | `Subject_ID` (FK), `PCA_Component_1` … `PCA_Component_10`, `Null_Model_P`, `Motion_Noise_Residual` |
| **Regression_Result** | Summary of the linear model and permutation test. | `Model_ID`, `Beta_Variability`, `SE_Variability`, `Pearson_R`, `P_Value`, `R_Squared`, `N_Subjects`, `Covariates`, `Permutations`, `Timestamp`, `Significance_Status`, `FDR_Q_Value`, `FDR_Appplied`, `Subject_Results` |
| **Subject_Prediction** (nested in `Regression_Result`) | Per‑subject predicted scores and residuals for FR‑007 compliance. | `Subject_ID`, `Flexibility_Score`, `Predicted_Score`, `Residual` |

## Data Flow
1. **Raw ingestion** → `data/raw/` (checksums).  
2. **Parcellation** → regional time‑series (`data/processed/{subj}_ts.npy`).  
3. **Quality filtering** → `exclusion_log.csv` (SC‑001).  
4. **Dynamic connectivity** → `variability_metrics.csv` (Subject + PCA components).  
5. **Null‑model validation** → `null_validation.csv` (`Null_Model_P`).  
6. **Regression & permutation** → `regression_summary.json` (output schema).  
7. **Final merge** → `final_results.csv` (subject‑level results, FR‑007).  

All CSV/JSON files are validated against the schemas in `contracts/`.

## Constraints
* **No nulls** in required columns (`Subject_ID`, `Age`, `Sex`, `Mean_FD`, `Total_Scan_Time`, `Flexibility_Score`, `PCA_Component_1`, `Status`).  
* **Value ranges**: `Mean_FD` ≥ 0, `Age` > 0, `Sex` ∈ {`"M"`, `"F"`}.  
* **Data types** must match the schema exactly (e.g., integers vs. floats).  

---
