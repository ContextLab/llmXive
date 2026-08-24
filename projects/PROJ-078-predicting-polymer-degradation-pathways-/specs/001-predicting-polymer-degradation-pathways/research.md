# Research: Polymer Degradation Pipeline Feasibility Study

## Summary

This research phase validates the feasibility of processing polymer structures using a lightweight GNN pipeline on CPU-only infrastructure. It confirms the availability of open-source datasets containing polymer SMILES but **explicitly confirms the absence** of degradation pathway labels (hydrolysis, oxidation, photolysis) and environmental conditions in these open sources. 

The project scope is therefore reduced to a **Feasibility Study**: validating the data ingestion, graph conversion, and attribution generation infrastructure using available SMILES data. The study does **not** attempt to predict degradation pathways or validate structure-mechanism relationships, as no ground truth exists.

## Dataset Strategy

The project relies on open, programmatically accessible datasets. The spec assumes the existence of a substantial collection of polyester degradation records in NIST and Materials Project. However, the "Verified datasets" block provided in the input contains **no verified source** for polymer degradation records, NIST Chemistry WebBook API data, or Materials Project data with degradation labels.

**Critical Finding**: The provided verified dataset list contains:
- `maykcaldas/smiles-transformers` (SMILES only): https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet
- `HUBioDataLab/SELFormer-smiles` (SMILES only): https://huggingface.co/datasets/HUBioDataLab/SELFormer-smiles/resolve/main/data.csv

These datasets contain **only SMILES strings**. They lack:
1.  **Degradation Pathway Labels** (hydrolysis, oxidation, photolysis).
2.  **Environmental Conditions** (temperature, pH, UV exposure).

**Resolution**: Since the spec requires "degradation records from NIST Chemistry WebBook and Materials Project" but the verified list does not contain these specific records, and the spec's assumption about data availability is conditional ("if not, the project scope is limited"), the plan adopts the following strategy:
1.  **Primary Attempt**: Download the available SMILES datasets (`maykcaldas/smiles-transformers`, `HUBioDataLab/SELFormer-smiles`) to test the ingestion and graph conversion pipeline.
2.  **Gap Acknowledgement**: Explicitly state that the *degradation pathway labels* and *environmental conditions* are **missing** from these open datasets.
3.  **Fallback/Feasibility Study**: The implementation will demonstrate the *structure* of the data ingestion pipeline (FR-001) using the available SMILES data. The model will be initialized but **not trained** to predict degradation pathways (as no labels exist). Instead, the study will:
    -   Generate attribution maps on a *randomly initialized* model to verify the code path works.
    -   Perform a χ² test on the distribution of structural motifs to validate data quality.
    -   Flag all records as `missing_pathway` (FR-008).
4.  **Power Analysis**: If the usable dataset (available SMILES count) is <150, the system triggers the power analysis warning (SC-004) and switches to Leave-One-Out Cross-Validation (LOOCV) for the feasibility study.

**Verified Datasets Reference**:
- `maykcaldas/smiles-transformers` (SMILES only): https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet
- `HUBioDataLab/SELFormer-smiles` (SMILES only): https://huggingface.co/datasets/HUBioDataLab/SELFormer-smiles/resolve/main/data.csv

*Note: No verified URL exists for the specific NIST/Materials Project degradation records mentioned in the spec. The implementation will handle this by flagging the data gap and proceeding with available SMILES data for structural analysis, while noting the inability to validate pathway prediction without ground-truth labels.*

## Methodological Rationale

### 1. Model Architecture (FR-003)
- **Choice**: 3-layer Graph Convolutional Network (GCN) with hidden dimension 128.
- **Rationale**: Fits within CPU memory constraints (≤7GB RAM). 3 layers are sufficient to capture local chemical environments (bonds, functional groups) without over-smoothing.
- **Hardware**: CPU-only (`device="cpu"`). No GPU fallback needed as the model is explicitly lightweight.
- **Training Status**: The model is **not trained** to predict degradation pathways (no labels). It is used in a *randomly initialized* state to demonstrate the attribution code path.

### 2. Data Augmentation vs. Imputation (FR-004)
- **Strategy**: **NO AUGMENTATION**.
- **Rationale**: Bond rotation changes conformation (3D geometry) but not connectivity (topology), which is what GNNs typically use. Atom masking removes atoms, fundamentally altering the molecule's identity and potentially its degradation pathway. Augmenting a dataset of specific polymers by destroying their chemical identity (masking) or changing their conformation (rotation) introduces noise that does not represent the true distribution of polymer degradation, invalidating the statistical generalization. The plan preserves chemical integrity by using the raw data only.
- **Imputation Rationale**: Missing environmental variables (pH, temp) are imputed with community-standard defaults (e.g., pH 7, 298K) and **flagged** as `imputed`. This is necessary to maintain a fixed feature vector size for the GNN. Unlike augmentation, imputation preserves the identity of the specific polymer instance while filling missing metadata. It does not create new synthetic molecules.
- **Feasibility**: No augmentation time required.

### 3. Feature Attribution (FR-005)
- **Method**: Integrated Gradients.
- **Rationale**: Provides a theoretically grounded attribution of the model's prediction to specific atoms/bonds.
- **Constraint**: Must run on CPU; Integrated Gradients is computationally intensive but feasible for small graphs and limited dataset size.
- **Validation**: The attribution is generated on a *randomly initialized* model to verify the code path works. **No scientific validity** is claimed for the attribution scores. The test validates that the algorithm runs without error, not that it identifies chemical mechanisms.

### 4. Statistical Validation (FR-006, SC-002, Constitution VI)
- **Method**: **χ² Test** (Constitution Principle VI) and **Null Attribution Test**.
- **Procedure**:
    1.  **χ² Test**: Analyze the distribution of structural motifs (e.g., ester bonds, aromatic rings) in the available data to check for non-random distribution. This validates *data quality* (ensuring the dataset contains a mix of motifs), not mechanism prediction. This satisfies Constitution Principle VI's requirement for a statistical test.
    2.  **Null Attribution Test**: Shuffle node features to verify the attribution mechanism does not assign high importance to random noise. This validates the *attribution algorithm*, not a chemical hypothesis.
- **Rationale**: Validates the pipeline's technical correctness without requiring ground truth labels.
- **Constraint**: Must run on CPU; feasible for small datasets.

### 5. Cross-Validation Strategy
- **Method**: 
    - **n ≥ 150**: 5-fold Cross-Validation.
    - **50 ≤ n < 150**: 5-fold Cross-Validation with a **power analysis warning** (SC-004).
    - **n < 50**: Leave-One-Out Cross-Validation (LOOCV) as per Constitution Principle VII.
- **Rationale**: Provides robust performance estimates for the feasibility study (e.g., inference stability). Aligns with Constitution Principle VII and SC-004.
- **Constraint**: Computationally feasible on CPU for small n.

## Compute Feasibility

- **CPU-First**: All methods (GCN, Integrated Gradients, χ² Test) are selected for their ability to run on a 2-core CPU within 6 hours.
- **Memory**: The model size (≤128 hidden dim) and dataset size (available SMILES count) ensure memory usage stays well below 7GB.
- **Disk**: Streaming data from Hugging Face and storing processed graphs in compressed formats (pickle/parquet) ensures disk usage remains within efficient operational limits.
- **No GPU Needed**: The spec explicitly requires CPU-only training. The "GPU escape hatch" is not needed as the model is designed to be lightweight.

## Risk Assessment

- **Data Gap**: The primary risk is the lack of verified open datasets with *both* SMILES and *degradation pathway labels*. The plan mitigates this by:
    1.  Using available SMILES data for structural analysis.
    2.  Clearly documenting the label gap.
    3.  Reframing the project as a feasibility study for the pipeline architecture.
- **Small Sample Size**: The plan includes a power analysis warning if the available SMILES count is <150. No data augmentation is performed to avoid introducing chemical noise.
- **Computational Limits**: The model architecture and processing strategy are explicitly designed to fit within the 6-hour, 7GB RAM constraint.
