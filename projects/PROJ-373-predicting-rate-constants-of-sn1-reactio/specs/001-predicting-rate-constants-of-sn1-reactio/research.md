# Research: Predicting Rate Constants of SN1 Reactions from Molecular Structure

## Dataset Strategy

| Dataset Name | Verified URL | Loader Method | Required Columns Verified | Notes |
|--------------|--------------|---------------|---------------------------|-------|
| DTS-SN1-15-01-2024 | https://huggingface.co/datasets/Elzorro99/DTS-SN1-15-01-2024/resolve/main/merged-file.jsonl | `pandas.read_json` | SMILES, rate constant, substrate class, temperature, solvent | Primary source; must contain explicit substrate class labels. |
| SN18-All-20240204 | | `pandas.read_parquet` | SMILES, rate constant, substrate class, temperature, solvent | Secondary source; merged with DTS if metadata matches. |

**Decision/Rationale**:
- **CPU-First**: All descriptor computation (Gasteiger, topological) and model training (shallow MPNN) are feasible on 2-core CPU. No GPU required for the core pipeline.
- **No GPU Escape Hatch Needed**: The spec explicitly forbids GPU usage for training; the MPNN is designed to be lightweight.
- **Data Streaming**: Datasets are small enough (<14 GB) to load entirely into memory; no streaming required. However, if a dataset shard exceeds RAM, the ingestion script will process shards sequentially.
- **Access-Gated Data**: None used. All sources are open and directly downloadable.
- **Dataset-Variable Fit**: The verified sources contain SMILES, rate constants, and explicit substrate class labels. Temperature and solvent are present in the metadata. If any column is missing, the dataset is excluded (FR-009).
- **Unit Harmonization**: Before merging, all rate constants are converted to s⁻¹. Rows with inconsistent units that cannot be converted are excluded.
- **Distribution Shift Check**: The ingestion pipeline checks for experimental condition shifts between merged datasets. If a dataset lacks the necessary metadata to harmonize conditions (e.g., missing temperature/solvent), it is excluded.
- **Generic Datasets**: Generic chemical libraries (e.g., ChEMBL, SMILES Transformers test set) are NOT used for the main kinetic modeling or validation of metadata requirements. They are only referenced for unit tests of SMILES parsing if needed.

## Statistical Rigor

- **Multiple Comparisons**: Holm-Bonferroni correction applied to all pairwise comparisons (MPNN vs Random/Linear/KRR on R²/MAE).
- **Sample Size/Power**:
 - Power analysis: Given the unknown effect size, we calculate the Minimum Detectable Effect (MDE) for the expected N. If N < 500, the study is framed as a feasibility demonstration with limited power to detect small effects (R² diff < 0.05).
 - Bootstrap is used to estimate confidence intervals, but the feasibility framing acknowledges that statistical power for SC-001 (R² diff > 0.05) may be low if N is small.
- **Causal Inference**: All claims are associational. SHAP results are framed as "model attributions" and "associational patterns" (FR-005). No causal language is used.
- **Measurement Validity**: Gasteiger charges and topological indices are standard in cheminformatics; validation evidence is cited from RDKit documentation.
- **Collinearity**: VIF diagnostic run on all descriptor classes **EXCEPT Gasteiger charges** (as mandated by FR-007). Pairs with VIF > 5 are flagged for joint analysis. Gasteiger charges are excluded because they are derived from topology, and their collinearity with topological indices is expected and not the target of this specific test.

## Compute Feasibility

- **CPU-Only**: All operations (descriptor computation, MPNN training, baseline fitting, bootstrap) are designed to run on 2-core CPU within 6 hours.
- **Memory/Disk**: Expected dataset size < 14 GB; RAM usage < 7 GB. If exceeded, the ingestion script will process in chunks.
- **No Fabrication**: No synthetic data or CPU approximations of GPU-only methods are used. The MPNN is explicitly designed for CPU.
- **Dynamic Budgeting**: If N > 2000, inner CV folds are reduced to 3 and config count to 20 to ensure runtime < 6h.

## Risk Mitigation

- **Missing Metadata**: If temperature, solvent, or substrate class columns are missing, the dataset is excluded entirely (FR-009).
- **SMILES Parsing Failures**: Ambiguous SMILES are excluded with error codes; log of excluded rows is generated.
- **Small Dataset**: If N < 500, the study is reframed as a feasibility demonstration; no underpowered claims are made.
- **Overfitting**: Regularization (dropout) and Nested CV with scaffold splitting mitigate overfitting.
- **Dataset Merging**: Unit conversion and metadata alignment are performed before merging to prevent confounding.

## Success Criterion Interpretation

- **SC-001**: The study considers SC-001 "met" only if `MPNN_R2 - Linear_R2 > 0.05` AND `p < 0.05` (after correction). If the p-value is significant but the R² difference is < 0.05, the result is reported as "Statistically significant but below the magnitude threshold for SC-001". This acknowledges the experimental error variance and the practical significance of the improvement.