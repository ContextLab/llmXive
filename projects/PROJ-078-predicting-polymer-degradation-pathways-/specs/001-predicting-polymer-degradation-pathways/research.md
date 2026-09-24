# Research: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Executive Summary

This research investigates the feasibility of using Graph Neural Networks (GNNs) to detect structural rules in a **simulated environment**. Due to the scarcity of labeled experimental data in public repositories, this study employs a **synthetic labeling strategy** where degradation labels are generated based on known chemical rules (e.g., "aromatic rings -> photolysis"). The primary goal is **not** to predict real-world degradation pathways, but to validate the pipeline's consistency: ensuring the GNN can successfully learn the synthetic rules and that the statistical tests (χ²) confirm this learning. The approach prioritizes reproducibility on CPU-only hardware, adhering to the project's constraint of ≤7GB RAM and ≤6h runtime.

**Critical Scope Note**: This study is a **Simulation of a Simulation**. It validates the *pipeline's ability to detect structural rules* rather than predicting actual chemical degradation mechanisms. All findings are framed as "synthetic rule consistency" and not as "scientific discovery of real-world phenomena."

## Dataset Strategy

### Verified Datasets
The following datasets are the **only** sources used for data ingestion, as verified by the project's "Verified datasets" block:

| Dataset Name | Type | Verified URL | Relevance to Spec |
|:--- |:--- |:--- |:--- |
| **SMILES Transformers Test** | Parquet | ` | Source of polymer SMILES strings. Contains molecular structures that can be filtered for polyesters. |
| **HUBioDataLab SELFormer** | CSV | ` | Supplementary source for SMILES strings and potential functional group annotations. |
| **NIST (jsonl)** | JSONL | ` | *Note: This dataset appears to be NIST 800-53 security controls, not Chemistry WebBook.* **Action**: The spec requests NIST Chemistry WebBook, but the verified block contains a security dataset. The plan will attempt the specified API, log the failure, and proceed with the **SMILES** datasets for structure and **simulate** the environmental conditions (pH, Temp, UV) based on the spec's assumption of "community-standard defaults" where missing, as no verified chemistry degradation dataset exists in the block. |
| **WebBook (csv)** | CSV | ` | *Note: This appears to be a text corpus of books, not the NIST Chemistry WebBook.* **Action**: As with the NIST dataset, no verified chemical degradation dataset is available in the block. The project will proceed using the **SMILES** datasets for structure and apply **synthetic environmental labels** as per the spec's "Assumption about data availability". |

> **Critical Gap Resolution**: The spec explicitly assumes that "NIST Chemistry WebBook and Materials Project APIs lack sufficient polyester records with documented degradation products." The verified dataset block confirms this gap: the available NIST/WebBook links point to non-chemical datasets (security controls, book text). Therefore, the **primary data strategy** is:
> 1. **Attempt Specified Sources**: Attempt to fetch from the specified NIST/Materials Project APIs.
> 2. **Log Failure**: If the returned data is non-chemical, log a `Source Mismatch` error.
> 3. **Manual Override**: Proceed with the **SMILES** datasets only if a manual override flag is provided.
> 4. **Ingest SMILES**: Ingest SMILES from `maykcaldas/smiles-transformers` and `HUBioDataLab/SELFormer`.
> 5. **Filter**: Filter for polyesters using RDKit (functional group detection).
> 6. **Synthesize**: **Synthesize** environmental conditions (Temp, pH, UV) and degradation labels based on the spec's "synthetic label distribution" requirement, as no ground-truth degradation dataset is accessible via the verified URLs.
> 7. **Flag**: Flag all records as "synthetic" in the metadata for transparency.

### Data Mismatch Warning
**Critical Note**: The SMILES datasets used (`maykcaldas/smiles-transformers`, `HUBioDataLab/SELFormer-smiles`) are general chemical language model training sets, not curated polymer degradation repositories. They lack specific 'polyester' functional group annotations and, critically, the 'degradation pathway' labels (hydrolysis/oxidation/photolysis) required by the spec. The plan admits to synthesizing these labels. Using a general SMILES dataset as the *only* structural source for a specific polymer degradation study introduces a fundamental data mismatch: the chemical space in these datasets may not represent the specific polyester degradation mechanisms the model is intended to predict, rendering the synthetic labels scientifically ungrounded. **This study is a Simulation of a Simulation, not a predictor of real-world degradation.**

### Data Ingestion Pipeline (FR-001, FR-002, FR-008, FR-009)
1. **Download**: Fetch SMILES datasets via `datasets.load_dataset` (Hugging Face) or direct `pandas.read_parquet`/`read_csv`.
2. **Filter**: Use RDKit to identify polyester functional groups (`C(=O)O` patterns) in SMILES.
3. **Handle Missingness**:
 * If environmental data is missing (which it will be, as the source is just SMILES), assign defaults: pH=7, Temp=25°C, UV=0.
 * Log the assignment and flag the record as `synthetic_env`.
4. **Label Generation**:
 * Assign degradation labels (hydrolysis, oxidation, photolysis) based on a synthetic distribution (e.g., hydrolysis as a dominant category, with oxidation and photolysis represented proportionally) or specific structural rules (e.g., aromatic rings -> photolysis).
 * Log the label source as `synthetic`.
5. **Validation**: If the filtered dataset size < 150, trigger a power analysis warning (SC-004) and switch to Leave-One-Out (LOO) validation (FR-009).

## Model Architecture & Training (FR-003, FR-004, FR-005)

### Architecture
* **Type**: Graph Convolutional Network (GCN) or GraphSAGE.
* **Layers**: ≤3 layers (to fit CPU memory and prevent over-smoothing).
* **Hidden Dimension**: ≤128.
* **Input Features**:
 * Node: Atom type, degree, hybridization, formal charge (from RDKit).
 * Edge: Bond type, conjugation, aromaticity.
 * Global: Environmental vector [pH, Temp, UV] concatenated to node features or used as a graph-level condition.
* **Output**: Softmax over 3 classes (Hydrolysis, Oxidation, Photolysis).

### Training Strategy
* **Hardware**: CPU-only (GitHub Actions).
* **Optimization**: Adam optimizer, Learning Rate = 0.001.
* **Validation**:
 * If n ≥ 150: 5-fold Cross-Validation (SC-001, verified source `2604.10702`).
 * If n < 150: Leave-One-Out (LOO) validation (FR-009).
* **Augmentation**:
 * **Edge Dropout**: Randomly drop edges (prob=0.1) to simulate bond instability.
 * **Subgraph Sampling**: Sample subgraphs to increase dataset size by 2x (FR-004).
 * **Constraint**: Augmentation must complete within 30 minutes (SC-009).

### Feature Attribution (FR-005)
* **Method**: Integrated Gradients (IG).
* **Baseline**: Zero vector or a "saturated" graph.
* **Target**: Identify atoms/bonds contributing most to the predicted degradation class.
* **Validation**: Verify that ester linkages are highlighted in top attribution scores for hydrolysis cases (SC-005). **Correction**: This is a **Self-Consistency Check** to confirm the model learned the synthetic rules, not a discovery of real chemical mechanisms.

## Statistical Validation (FR-006, SC-002)

### χ² Test for Significance (Pipeline Consistency Test)
* **Null Hypothesis**: The observed motif importance scores are not different from a random distribution.
* **Method**:
 1. **Binning**: Convert continuous attribution scores into categorical bins (e.g., "High Importance" vs "Low Importance") to satisfy the χ² test's requirement for categorical data. Alternatively, use a **Kolmogorov-Smirnov (KS) test** for continuous scores.
 2. Generate a null distribution by shuffling motif labels repeatedly. (FR-006).
 3. Calculate χ² statistic for the observed motif-importance correlation.
 4. Compute p-value: `p = (count(null_stat >= obs_stat) + 1) / (iterations + 1)`.
* **Threshold**: α = 0.05 (Principle VI).
* **Outcome**: Report p-value and reject null if p < 0.05 (SC-011). **Scope**: This test validates **Pipeline Consistency** (i.e., "Did the model learn the synthetic rule?"), not real-world chemical correlations.

### Confidence Flagging (SC-008)
* **Threshold**: Predictions with softmax probability < 0.6 are flagged as "low confidence" (verified source `2312.01650`).
* **Action**: These predictions are excluded from the final motif ranking or explicitly marked in the report.

## Risk Assessment & Mitigation

| Risk | Impact | Mitigation Strategy |
|:--- |:--- |:--- |
| **Dataset Size < 150** | High (Model overfitting, LOO required) | Implement automatic LOO switch (FR-009). Report power analysis warning (SC-004) using `statsmodels` as a G*Power proxy. Use heavy augmentation (FR-004). |
| **No Ground Truth** | High (Synthetic labels may not reflect reality) | Explicitly flag all labels as "synthetic" in metadata. Frame results as "simulation-based" (Assumption). **This study is a Simulation of a Simulation.** |
| **CPU Memory Limit** | High (OOM during training) | Use small batch sizes, ≤128 hidden dim, and streaming data loading if possible. |
| **Invalid SMILES** | Medium (Pipeline crash) | RDKit validation with skip-and-log strategy (FR-009). |
| **Source Mismatch** | High (Spec requires NIST, data is non-chemical) | Implement Data Validity Check. Log `FATAL` error if source is non-chemical. Require manual override to proceed with synthetic data. |
