# Research: Predicting Molecular Conductivity from Graph-Based Features

## Dataset Strategy

The project relies on verified datasets containing SMILES strings and conductivity (or proxy) values. Per the input constraints, only the following verified sources are used:

| Dataset Name | Description | Verified URL | Usage Plan |
|:--- |:--- |:--- |:--- |
| **SMILES Transformers Test** | Contains SMILES strings. | ` | Source of molecular graph structures. |
| **HOMO-LUMO** | Contains HOMO-LUMO gaps (quantum descriptor). | ` | Primary target source (if conductivity missing). |
| **MAESTRO** | Contains molecular geometries and properties. | ` | Backup source for structural properties. |
| **PubChem** | Large scale SMILES. | ` | Backup source for SMILES. |

**Critical Dataset Fit Assessment**:
The specification requires a dataset with **SMILES strings AND measured/DFT-derived conductivity values**.
- The **SMILES Transformers** dataset provides SMILES but lacks conductivity labels.
- The **HOMO-LUMO** dataset provides a quantum descriptor (gap) but lacks explicit conductivity.
- **DFT-derived** conductivity has **NO verified source** in the input block.

**Decision**: The plan implements a **reframing strategy** based on verified data:
1. **Check for Conductivity**: Load datasets to check for a conductivity column.
2. **If Conductivity Missing**:
 - Use the **HOMO-LUMO** dataset's gap as the target variable.
 - **Reframe Research Question**: The study will predict "Electronic Delocalization Potential (HOMO-LUMO Gap)" rather than "Conductivity."
 - **Explicit Warning**: Log "Target variable is HOMO-LUMO gap, not conductivity. Claims are limited to electronic structure prediction."
3. **If No Target Found**:
 - **HALT** pipeline with error: "No verified dataset found with required target variable (conductivity or HOMO-LUMO gap)."
4. **No Fabrication**: Do NOT invent a URL for a "Materials Project" or "PubChem conductivity" dataset.

*Note: The plan does NOT assume a correlation between HOMO-LUMO gap and conductivity without evidence. The study is framed as investigating the correlation between topology and the available target.*

## Methodological Rationale

### Descriptor Selection (FR-001, FR-008)
To address the reviewer's concern about resonance (linus-pauling-simulated), the descriptor set will include:
- **Topological**: Degree distribution, average path length, ring count.
- **Resonance/Aromaticity**: Aromatic ring count, Hückel aromaticity index, and **Longest Conjugated Path Length** (computed as the longest simple path in the subgraph induced by conjugated bonds).
- **Quantum Proxy**: If available in the verified dataset, HOMO-LUMO gap. If not, the topological conjugation length serves as the proxy.

**Validation Check**: Before training, compute correlation between topological descriptors and the target. If correlation is weak, log a warning that the topological proxy hypothesis may be unsupported.

### Model Strategy (FR-002, FR-003)
- **Splitting**: Scaffold splitting using `rdkit.Chem.Scaffolds.MurckoScaffold` to ensure structural diversity between train and test sets.
- **Algorithms**: Random Forest (RF) and Gradient Boosting (GB) regressors. These are CPU-tractable and robust to non-linear relationships.
- **Target Transformation**:
 - Check target distribution.
 - Apply log-transformation ONLY if the target exhibits a log-normal distribution or >3 orders of magnitude range.
 - Otherwise, use raw values and document distributional properties.

### Statistical Rigor (FR-006, FR-013, SC-004, SC-007)
- **Collinearity**: Variance Inflation Factor (VIF) calculated for all predictors. Features with VIF > 10 are excluded, and the model is **retrained** on the reduced set (iterative loop).
- **Multiple Comparisons**: Benjamini-Hochberg procedure applied to p-values of feature-conductivity correlations to control False Discovery Rate (FDR) at a standard significance threshold.
- **Sensitivity**:
 - **Retrain Loop**: Retrain models for each outlier threshold in a range of standard deviations.
 - **Statistical Test**: Perform ANOVA or Kruskal-Wallis on R² scores across thresholds to determine if variance is significant.

### Compute Feasibility
- **Memory**: Datasets are loaded in chunks or sampled if > 5000 rows to fit 7 GB RAM.
- **Time**: Random Forest and GB on <5000 samples with <20 features will complete in minutes, well within the 6-hour limit.
- **No GPU**: All libraries (`scikit-learn`, `rdkit`) are CPU-native.

## Decision Log

| Decision | Rationale |
|:--- |:--- |
| Reframe Target to HOMO-LUMO Gap | Verified datasets lack conductivity. HOMO-LUMO gap is the best available proxy for electronic properties. Claims are limited to electronic structure. |
| Conditional Log-Transformation | Log-transformation is only applied if distributional properties justify it, avoiding bias from inappropriate transformation. |
| Iterative VIF Retraining | Required by FR-013 to ensure final model is trained on independent features. |
| Sensitivity Retrain Loop | Required by FR-007 to measure actual model performance variance, not just post-hoc filtering. |
| Statistical Significance Test | Required to determine if variance across outlier thresholds is meaningful, not just descriptive. |
| Pre-training Correlation Check | Validates the topological proxy hypothesis before investing in model training. |
| Project Halt Condition | Prevents invalid analysis if no valid target variable exists in verified datasets. |