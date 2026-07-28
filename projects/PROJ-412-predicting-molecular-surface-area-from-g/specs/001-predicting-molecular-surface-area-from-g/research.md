# Research: Predicting Molecular Surface Area from Graph Convolutional Networks

## Problem Statement

Can a Graph Convolutional Network (GCN) trained solely on 2D molecular topology predict the 3D solvent-accessible surface area (SASA) of a molecule with accuracy comparable to a baseline that explicitly computes 3D geometry? This study quantifies the information loss inherent in 2D-only representations for this specific physical property. The baseline is defined as the direct computation of SASA via RDKit on the test set (the "Geometry Oracle"), representing the theoretical limit of 3D-based prediction.

## Dataset Strategy

### Verified Datasets
The project relies exclusively on the following verified, open-access datasets. No access-gated data (e.g., ADNI, ZINC15 raw portal) is used.

| Dataset Name | Source URL | Usage | Notes |
|:--- |:--- |:--- |:--- |
| **ChEMBL-2025 Randomized** | ` | Primary Training Data | Contains SMILES. **SASA is NOT present**; it is derived by the pipeline. |
| **ZINC15 Processed** | ` | Secondary Validation | Community upload; validated via checksum/schema check (T003). |
| **RDKit Chemical** | ` | Supplemental | Backup source for diverse chemical space. |

**Dataset Selection Rationale**:
The ChEMBL-2025 dataset is selected as the primary source because it is a direct, verified Hugging Face Parquet file that is programmatic download-friendly. It contains clean SMILES strings, which are the required input for RDKit. The dataset size is unknown but assumed to be large; the plan includes a **streaming strategy** (`datasets.load_dataset(..., streaming=True)`) to process molecules in chunks, ensuring the 7GB RAM constraint is never exceeded. If the full dataset is too large to process in the 6-hour CI limit, a fixed random sample will be drawn.

**Variable Fit Verification**:
- **SMILES**: Present in all verified sources.
- **Target (SASA)**: **NOT present** in the raw dataset. The plan explicitly generates this label using RDKit's `rdkit.Chem.rdMolDescriptors.CalcSASA()` on generated 3D conformers. This aligns with **Assumption about ground truth** in the spec: the "ground truth" is a computed value, not experimental.
- **Discarded Proxy**: `CalcTPSA()` (Topological Polar Surface Area) is explicitly **discarded** as a label source. TPSA is a 2D descriptor and does not represent the 3D geometric property (SASA) required by the research question.
- **Predictors**: 2D graph features (atom type, hybridization, degree) will be extracted from SMILES using RDKit.

**Data Availability Plan**:
1. **Download**: Use `datasets` library to stream the Parquet file.
2. **Validation**: Check for `NaN` in SMILES column. Log and exclude invalid entries.
3. **3D Generation**: For each SMILES, generate a 3D conformer using `rdkit.Chem.AllChem.EmbedMolecule`. If generation fails (>10% failure rate), the pipeline generates a failure report analyzing the properties of failed molecules to assess selection bias.
4. **Labeling**: Compute SASA from the 3D conformer using `CalcSASA`.
5. **Storage**: Save processed pairs (SMILES, Graph Features, SASA) to `data/processed/paired_dataset.parquet`.

## Methodological Rigor

### Statistical Approach
1. **Baseline (Geometry Oracle)**: The baseline is the direct computation of SASA via RDKit on the test set. This represents the "3D truth". The comparison is between the GCN prediction and this direct 3D computation.
2. **GCN Model**: A 3-layer Graph Convolutional Network (GCN) using PyTorch Geometric. Input: 2D graph (nodes=atoms, edges=bonds). Output: Scalar SASA.
3. **Comparison**: Since the baseline error is zero (by definition of the Oracle), the statistical test is a one-sample test on the GCN errors against zero.
 - **Assumption Check**: Perform Shapiro-Wilk test on the distribution of GCN errors.
 - **Test**: If normal, use one-sample t-test. If not, use Wilcoxon signed-rank test.
4. **Multiple Comparison Correction**: For the sensitivity analysis (testing thresholds {0.01, 0.05, 0.1}), a Bonferroni correction will be applied to the p-values of the success rates.

### Sample Size & Power
- **Power Justification**: The study will use a dataset subset sampled to fit the memory budget (typically 10k-50k molecules). Given the lack of prior variance estimates for this specific 2D-to-3D prediction task, a formal a priori power analysis is not feasible. The study will report the observed effect size and confidence intervals, acknowledging the limitation of not having a priori variance estimates. Post-hoc power analysis will be included in the final report.

### Robustness & Sensitivity
- **Threshold Sweep**: Evaluate success rate (prediction within X Å²) at X = {0.01, 0.05, 0.1} Å² (absolute values as per spec).
- **Sensitivity Check**: Plot success rate vs. threshold to demonstrate robustness.
- **Conformer Stability**: Record the number of conformer generation attempts. If >10% fail, generate a failure report analyzing the properties of failed molecules (e.g., MW, atom count) to assess if exclusion introduces bias.

## Decision/Rationale: CPU vs GPU
- **Choice**: **CPU-First**.
- **Rationale**: The GCN architecture is lightweight (3 layers, <1M params). Training on 50k molecules with batch size 64 fits comfortably within 7GB RAM on a 2-core CPU. PyTorch Geometric has efficient CPU backends.
- **GPU Escape Hatch**: Not required. If the dataset size grows unexpectedly (>100k molecules), the plan uses streaming and batching, which scales linearly with time but not memory. No CUDA kernels are needed.

## Risk Mitigation
- **Risk**: RDKit 3D conformer generation fails for >10% of molecules.
 - **Mitigation**: Increase `maxAttempts` and `numThreads` in RDKit. If failure rate remains high, generate a failure report analyzing the properties of failed molecules. If >10%, the pipeline halts with a warning, but the report is generated to document the bias.
- **Risk**: Memory overflow during graph extraction.
 - **Mitigation**: Process molecules in chunks of [deferred]. Clear memory after each chunk. Use `streaming=True` for dataset loading.
- **Risk**: Dataset lacks sufficient chemical diversity.
 - **Mitigation**: Verify molecular weight distribution in the test set against the training set (KS test p-value > 0.05). If failed, re-sample.
