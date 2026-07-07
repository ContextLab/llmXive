# Research: Predicting Polymer Degradation Pathways with Graph Neural Networks

## Problem Statement

The goal is to predict polymer degradation pathways (hydrolysis, oxidation, photolysis) from molecular structure (SMILES) and environmental conditions (temperature, pH, UV) using a Graph Neural Network. The dataset is observational (no random assignment), so all findings are framed as associational. The model must run on free-tier CI (CPU-only, ≤7GB RAM, ≤6h).

**Critical Data Gap**: The source spec assumes the existence of a dataset with explicit "degradation pathway" labels. No verified source currently provides this specific combination of polymer structure, environmental conditions, and degradation outcome labels. The plan includes a "Data Acquisition Protocol". If no verified source provides the target variable, the pipeline attempts manual curation. If curation fails, the project scope shifts to "Unsupervised Representation Learning" rather than halting.

## Dataset Strategy

### Verified Sources

| Dataset | URL | Format | Relevance | Limitations |
|---------|-----|--------|-----------|-------------|
| NIST Chemistry WebBook (WebBooks-1) | ` | CSV | Contains polymer records, SMILES | **Missing Target Variable**: Does not contain explicit "degradation pathway" labels (hydrolysis/oxidation). Used for **Pre-training** only. |
| SMILES (MKE Novel Druglike) | ` | CSV | Provides SMILES strings | **Missing Target Variable**: No degradation labels or environmental conditions. Used for **Pre-training** only. |
| SMILES (HUBioDataLab SELFormer) | ` | CSV | Additional SMILES data | **Missing Target Variable**: No degradation labels or environmental conditions. Used for **Pre-training** only. |

> **Critical Note**: The spec assumes NIST and Materials Project APIs contain ≥150 polyester degradation records with explicit labels. The verified dataset block does **not** list a direct NIST/Materials Project degradation dataset with the required target variable.

### Data Acquisition Protocol (New)

1. **Automated Extraction**: `ingest.py` attempts to extract records with explicit "degradation pathway" labels from the verified sources.
2. **Manual Curation Fallback**: If <50 labeled records are found:
 - The system triggers a manual curation step.
 - A script `code/curation_helper.py` generates a list of candidate polymers based on SMILES patterns.
 - A human curator (or automated literature search) extracts labels from primary literature (Google Scholar) for these candidates.
 - These records are saved to `data/raw/manual_curated.csv` with checksums and source citations.
3. **Ground Truth Verification**: A random sample of records (from automated or manual sources) is cross-referenced with primary literature. If the error rate > 10%, the dataset is rejected and the project shifts to "Unsupervised Representation Learning".
4. **Final Decision**:
 - If ≥50 labeled records exist: Proceed with Supervised Learning.
 - If <50 labeled records exist: Proceed with Semi-Supervised Pre-training (using unlabeled data) + Fine-tuning on small set.
 - If 0 labeled records exist: Shift scope to "Unsupervised Polymer Property Clustering" (reporting clusters of degradation-prone motifs without pathway labels).

### Data Ingestion Plan (FR-001, FR-008)

1. **Download**: Fetch `books_dataset.txt` (NIST) and SMILES CSVs via `requests` with exponential backoff (3 retries max).
2. **Filter**: Retain only records with:
 - SMILES containing ester functional groups (`C(=O)O`).
 - **Explicit** "degradation pathway" labels (hydrolysis, oxidation, photolysis).
3. **Validate**: Check for missing environmental variables (temp, pH, UV).
 - **Action**: If a record lacks a specific environmental variable, **EXCLUDE** it from the training set.
 - **Rationale**: Imputing defaults (e.g., pH 7) creates a massive confound where the model learns from missingness rather than chemistry. Records with missing critical environmental labels are dropped to preserve the validity of the structure-mechanism correlation (Corrected per amended FR-002).
4. **Output**: Write to `data/processed/polymer_graphs.csv` with columns: `smiles`, `temp`, `pH`, `uv`, `pathway`, `flags`.

### Model Architecture (FR-003, FR-005)

- **Type**: Lightweight GNN (Message Passing Neural Network).
- **Layers**: ≤3 GNN layers.
- **Hidden Dimension**: ≤128.
- **Input Features**:
 - Node: Atomic number, degree, hybridization, formal charge.
 - Edge: Bond type (single, double, aromatic), conjugation.
 - Global: Temperature, pH, UV (concatenated to node features or used as graph-level context).
- **Output**: Softmax over degradation pathways (hydrolysis, oxidation, photolysis, other).
- **Training**:
 - Loss: Cross-entropy.
 - Optimizer: Adam (learning rate [deferred]).
 - Epochs: 50 (early stopping if loss converges within 5% over last 5 epochs).
 - Validation: 5-fold CV (or LOO if n<50).
- **Feature Attribution**: Integrated Gradients (baseline: zero-atom graph). **Note**: IG is for interpretation only, not primary significance testing.

### Data Augmentation (FR-004 - Corrected)

- **Methods**:
 - **SMILES Canonicalization**: Handle representation variance by canonicalizing SMILES strings.
 - **Topological Noise Injection (Functional-Group-Preserving Edge Dropout)**: Randomly drop non-critical edges (e.g., single bonds not part of the ester linkage or the immediate alpha-carbon) to simulate minor structural noise. **Do not** rotate bonds or mask atoms, as this destroys the chemical validity of degradation pathways (Corrected per amended FR-004).
 - **Constraint**: The ester functional group (`C(=O)O`) and its immediate neighbors must remain intact to ensure the degradation pathway (hydrolysis) is not chemically altered.
- **Goal**: Expand training set ~2× within 30 minutes (only if n < 150).
- **Validation**: Compare macro-F1 on non-augmented vs. augmented baselines.

### Statistical Validation (FR-006, FR-007, SC-002, SC-005)

- **Two-Tier Validation Strategy**:
 1. **Global Model Significance (Label-Shuffling Permutation Test)**:
 - **Null Hypothesis**: "Structure does not predict pathway."
 - **Method**: Shuffle the *pathway labels* (Y) relative to the structures (X) 1000 times.
 - **Metric**: Compute macro-F1 for each permuted dataset.
 - **P-value**: Proportion of permuted macro-F1 scores ≥ observed macro-F1 score.
 - **Rationale**: This tests the existence of a structure-mechanism correlation, validating the *model's* predictive power.
 2. **Local Motif Significance (Motif-Masking Permutation Test)**:
 - **Null Hypothesis**: "Specific motifs do not drive the prediction."
 - **Method**: Mask specific subgraphs (e.g., ester bonds) identified by Integrated Gradients and measure the drop in prediction confidence. Compare this drop to the drop caused by masking *random* subgraphs of the same size.
 - **Metric**: Difference in prediction confidence (Masked Motif vs. Random Mask).
 - **P-value**: Proportion of random mask drops ≥ observed motif mask drop.
 - **Rationale**: This directly validates if *specific motifs* (not just the model) are significant, avoiding circularity.
- **χ² Discretization Protocol (Constitution VI Compliance)**:
 - To satisfy Constitution VI's requirement for a χ² test, we discretize continuous Integrated Gradients scores:
 - Bin IG scores into 'High Importance' (>90th percentile) vs 'Low'.
 - Create a contingency table: [High/Low IG] vs [True Pathway/Random Pathway].
 - Run χ² test at α=0.05.
 - **Note**: This is a secondary compliance test. The primary scientific validation is the Motif-Masking test.

### Motif Reporting

- Aggregate Integrated Gradients scores across test set (for interpretation only).
- Rank top 3-5 structural motifs (e.g., "aromatic ring proximity to ester bond").
- Flag predictions with confidence <0.6 as "low confidence".
- Report p-values from both the Label-Shuffle and Motif-Masking tests.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Dataset <150 instances** | Trigger power analysis warning; use LOO if n<50; report CI. |
| **Missing degradation labels** | **Manual Curation**: Attempt to extract labels from literature. If fails, shift to Unsupervised Clustering. |
| **Missing environmental data** | **EXCLUDE**: Records with missing temp/pH/UV are dropped to prevent confounding (Corrected per amended FR-002). |
| **Memory >7GB** | Subsample dataset; reduce hidden dimension; use batch processing. |
| **Runtime >6h** | Limit epochs; early stopping; reduce augmentation iterations. |
| **Invalid SMILES** | Skip record; log SMILES; continue processing (FR-002). |

## Decision Rationale

- **CPU-only**: Required for free-tier CI; GNN architecture constrained to ≤3 layers, dim ≤128 to fit memory.
- **Integrated Gradients**: Standard for feature attribution in GNNs; computationally feasible on CPU. **Used only for interpretation.**
- **Label-Shuffling Permutation Test**: Robust for small datasets; avoids parametric assumptions; correctly tests the null hypothesis "structure does not predict pathway".
- **Motif-Masking Permutation Test**: Directly validates motif significance without circularity by comparing against a random mask baseline.
- **Data Augmentation**: Necessary to mitigate overfitting on small sample sizes (Constitution VII), but must be chemically valid (no bond rotation/atom masking). **Corrected to use functional-group-preserving edge dropout.**
- **Exclusion of Missing Data**: Prevents the model from learning spurious correlations from missingness. **Corrected from imputation to exclusion.**
- **Semi-Supervised Fallback**: Allows the project to proceed scientifically even if labeled data is scarce, by leveraging large unlabeled datasets for representation learning.
