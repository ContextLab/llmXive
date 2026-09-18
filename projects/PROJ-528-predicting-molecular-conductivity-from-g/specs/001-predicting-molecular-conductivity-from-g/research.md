# Research: Predicting Molecular Conductivity from Graph-Based Features

## Research Question
Can graph-based topological descriptors (aromaticity, conjugation length, ring count) predict the **HOMO-LUMO gap** (a quantum mechanical property inversely related to electronic conductivity) with statistically significant accuracy, and which descriptors are robust predictors after controlling for collinearity?

**Note on Scope**: The original specification asked for "conductivity" (charge carrier mobility). However, no verified dataset exists containing experimental or DFT-derived "charge carrier mobility" for a large set of molecules with SMILES strings. Therefore, this study reframes the target to **HOMO-LUMO gap**, a standard proxy for intrinsic electronic delocalization and a prerequisite for conductivity. The results will be interpreted as predicting electronic properties of isolated molecules, not bulk conductivity (which depends on solid-state packing). This is a necessary deviation from the spec's FR-003, requiring a spec amendment.

### Scientific Objective Clarification
The study aims to predict a **quantum mechanical property** (HOMO-LUMO gap) from **topological descriptors**. This is distinct from predicting **bulk conductivity** (which depends on carrier density, mobility, and solid-state packing).
- **Predicting HOMO-LUMO**: Tests if graph topology can approximate quantum mechanical electronic structure. This is feasible with single-molecule descriptors.
- **Predicting Bulk Conductivity**: Requires modeling intermolecular interactions, crystal packing, and doping effects, which are not captured by single-molecule graph descriptors.
The plan explicitly focuses on the former (intrinsic molecular properties) and acknowledges the latter as a limitation.

## Dataset Strategy

The project relies on open, programmatic datasets. The primary challenge is finding a dataset that contains **both** SMILES strings and **measured or DFT-derived electronic properties** (HOMO-LUMO gap).

### Verified Datasets
Per the "Verified datasets" block and Principle II (Verified Accuracy), the following sources are available:

1. **QM9 Dataset (Primary Target)**:
 * **Source**: `qm9` via Hugging Face (`datasets.load_dataset('qm9')`).
 * **Verified URL**: `.
 * **Content**: Contains SMILES strings and DFT-derived HOMO-LUMO gaps for a large collection of small organic molecules.
 * **Fit**: Satisfies the requirement for a quantum-derived target variable (FR-014) and provides a large sample size for robust modeling.

2. **SMILES Sources (Supplemental)**:
 * `keanec27/Drug_Protein_Interactions_Smiles` (Parquet)
 * `maykcaldas/smiles-transformers` (Parquet)
 * *Note*: These are used only if QM9 lacks specific molecules, but QM9 is the primary source for the target.

### Dataset Fit & Limitations
* **Variable Fit**: The QM9 dataset contains SMILES and HOMO-LUMO gaps. It satisfies the requirement for a "quantum-derived descriptor" (FR-014) as the target.
* **Missing Data**: If QM9 is insufficient for a specific sub-problem, the project will fall back to topological proxies, but the primary model will be trained on the quantum-derived target.
* **Access**: QM9 is accessible via `datasets.load_dataset(..., streaming=True)`, satisfying the "open, directly-downloadable" constraint.
* **Limitation**: QM9 contains small molecules (up to 9 heavy atoms). The model's generalizability to larger, complex organic conductors is limited.

### Construct Validity & Limitations
* **Target Variable**: Using HOMO-LUMO gap as a proxy for conductivity is scientifically sound for *intrinsic* electronic properties (inversely related to excitation energy). However, it does not capture *bulk* conductivity, which depends on carrier density, mobility, and doping (solid-state effects).
* **Solid-State Effects**: Graph-based descriptors cannot capture intermolecular packing or morphology. The study explicitly acknowledges this limitation: it predicts the electronic properties of *isolated* molecules, not bulk material conductivity. This is a fundamental barrier to predicting bulk conductivity from single-molecule graphs.
* **Circularity**: The correlation between topological descriptors and HOMO-LUMO gap is not circular because HOMO-LUMO is a quantum mechanical calculation (DFT) derived from the wavefunction, whereas topological descriptors are graph-theoretic statistics. They share a common input (the molecular graph) but represent different levels of abstraction. The plan explicitly distinguishes between predicting a *computed* quantum property vs. a *measured* physical property to avoid circular validation.

### Statistical Independence
While topological descriptors and HOMO-LUMO gap share a common input (the molecular graph), they are not statistically dependent in a way that invalidates the correlation test. HOMO-LUMO is a quantum mechanical property derived from the electronic wavefunction, which is a solution to the Schrödinger equation. Topological descriptors are purely graph-theoretic. The study tests whether the *graph topology* can *predict* the *quantum property*, which is a non-trivial relationship. The potential for shared variance due to the common input is acknowledged, but the predictive power of the graph topology on the quantum property is the core research question.

## Statistical Methodology

### Model Training
* **Algorithms**: Random Forest (RF) and Gradient Boosting (GB) regressors.
* **Target**: Log-transformed HOMO-LUMO gap (proxy for intrinsic electronic conductivity).
* **Splitting**: Molecular Scaffold Splitting (using `rdkit.Chem.Scaffolds.MurckoScaffold`) to ensure structural diversity between train/test sets.
* **Validation**: 5-fold Cross-Validation on the training set.
* **Feature Selection**: **Nested Cross-Validation**. The VIF loop (FR-013) is performed *inside* the training fold to prevent data leakage. The final feature set is evaluated on the held-out test set.

### Rigor & Corrections
* **Multiple Comparisons**: Benjamini-Hochberg (BH) procedure applied to all feature-target correlation p-values (FR-006).
* **Collinearity**: Variance Inflation Factor (VIF) calculated for all features. Features with VIF > 10 are iteratively removed, and the model is retrained (FR-013). This is done within each CV fold to prevent overfitting (data dredging).
* **Sensitivity Analysis**: Model R² will be computed across outlier exclusion thresholds of 2.5σ, 3.0σ, and 3.5σ to assess robustness (FR-007).
* **Power**: The QM9 dataset provides >100,000 samples, ensuring high power to detect even small effect sizes.

## Compute Feasibility

* **CPU-First**: All models (RF, GB) and descriptors (RDKit) are CPU-tractable.
* **Memory**: Streaming the QM9 dataset and processing in batches ensures memory usage stays < 7 GB.
* **Time**: The pipeline (descriptors + 2 models + VIF loop + sensitivity sweep) is estimated to complete in < 3 hours on a 2-core runner, well within the 6-hour limit.
* **GPU Escape Hatch**: Not required. No deep learning (transformers) is planned for the core regression task.

## Decision/Rationale

* **Target Variable**: Using HOMO-LUMO gap as a proxy for conductivity is necessary because no verified dataset for "charge carrier mobility" exists. This satisfies FR-014 (quantum-derived descriptor) and the reviewer's concern about resonance (HOMO-LUMO captures electronic delocalization).
* **Topological Proxies**: If the quantum dataset were too small, topological proxies (conjugation length) would be computed on larger sets, but the primary validation will rely on the quantum target to ensure "Verified Accuracy".
* **VIF Loop**: The iterative VIF removal is essential to satisfy FR-013 and prevent spurious independent effects from collinear descriptors (e.g., ring count vs. aromaticity index). The nested CV approach prevents data dredging.
* **Constitutional Deviation**: The plan uses QM9 instead of Materials Project/PubChem as mandated by Principle VII. This is a necessary deviation due to the lack of the target variable in the mandated sources. A Constitution Amendment is required to formalize this exception.
* **Solid-State Limitation**: The plan explicitly acknowledges that graph-based descriptors cannot capture solid-state effects (packing, morphology) required for bulk conductivity. The results are interpreted as predicting intrinsic molecular electronic properties.