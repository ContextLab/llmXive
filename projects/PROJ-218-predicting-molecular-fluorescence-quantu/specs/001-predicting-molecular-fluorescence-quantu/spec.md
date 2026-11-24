# Feature Specification: Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks

**Feature Branch**: `001-predicting-molecular-fluorescence-quantum-yields`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Fluorescence Quantum Yields with Graph Neural Networks"

## User Scenarios & Testing

### User Story 1 - Data Curation and Preprocessing Pipeline (Priority: P1)

The researcher needs to ingest a public dataset of molecular structures (SMILES) and experimental fluorescence quantum yield (FQY) values, parse them into graph representations using RDKit, and split them into training, validation, and test sets using a scaffold-based strategy to ensure generalizability to unseen chemical spaces.

**Why this priority**: Without a clean, scaffold-split dataset, no model training can occur, and any subsequent results would suffer from data leakage, rendering the scientific inquiry invalid. This is the foundational step for all downstream analysis.

**Independent Test**: The pipeline can be fully tested by running the data ingestion script on a sample dataset and verifying that the output CSVs contain valid graph features, **raw experimental FQY values (ε‑clipped)**, and that the test set contains zero molecular scaffolds present in the training set.

**Acceptance Scenarios**:

1. **Given** a raw dataset file containing SMILES strings and FQY values, **When** the preprocessing script is executed, **Then** the output includes a training set, validation set, and test set where the test set scaffolds are disjoint from the training set.
2. **Given** a SMILES string with invalid syntax, **When** the preprocessing script processes it, **Then** the molecule is **excluded** from the dataset, and a **log entry records the exclusion reason** without crashing the pipeline.
3. **Given** the preprocessed data, **When** the feature extraction runs, **Then** every node in the molecular graph includes atom type, hybridization, and formal charge, and every edge includes bond type and conjugation status.
4. **Given** a synthetic test file that contains a molecule with a novel atom type (e.g., a lanthanide element not present in the training set), **When** the preprocessing script encounters it, **Then** the molecule is logged as “unseen atom type” and is **skipped** for inference but retained for evaluation, with a summary warning emitted at the end of the run (see FR-012).

---

### User Story 2 - GNN Model Training and Baseline Comparison (Priority: P2)

The researcher needs to train a lightweight Graph Neural Network (GNN) on the prepared dataset and compare its performance against a linear regression baseline using ECFP4 fingerprints to quantify the value of graph-based representations.

**Why this priority**: This step establishes whether the proposed GNN approach provides a tangible improvement over standard chemical descriptors. It validates the core hypothesis that static graph topology captures FQY variation better than traditional fingerprints.

**Independent Test**: The training process can be tested by executing the training script, which must complete within the 6-hour free-tier CI limit, and outputting performance metrics (R², RMSE, MAE) for both the GNN and the baseline on the held-out test set.

**Acceptance Scenarios**:

1. **Given** the scaffold-split training and validation sets, **When** the GNN model trains for up to 50 epochs with early stopping, **Then** the training process completes without GPU usage and the best model checkpoint is saved based on validation loss.
2. **Given** the test set, **When** the trained GNN and the linear regression baseline are evaluated, **Then** the system outputs R², RMSE, and MAE for both models, allowing for a direct performance comparison.
3. **Given** a model that fails to converge (validation loss increases for 10 consecutive epochs), **When** early stopping triggers, **Then** the system saves the weights from the epoch with the lowest validation loss rather than the final epoch.

---

### User Story 3 - Feature Attribution and Interpretability Analysis (Priority: P3)

The researcher needs to apply Integrated Gradients or SHAP to the trained GNN to identify and visualize the specific molecular substructures (e.g., conjugated systems, heteroatoms) that correlate most strongly with high or low fluorescence yields.

**Why this priority**: While prediction accuracy is important, the scientific value lies in understanding *which* structural features drive the predictions. This transforms the model from a black box into a tool for generating chemical design rules.

**Independent Test**: The interpretability module can be tested by running it on a subset of test molecules and generating feature importance scores that are visualized as bar charts or highlighted molecular graphs, confirming that the model focuses on chemically plausible substructures.

**Acceptance Scenarios**:

1. **Given** a trained GNN model and a test molecule, **When** the Integrated Gradients method is applied, **Then** the system outputs a ranked list of the **most influential substructures**, where substructures are defined as chemically meaningful fragments (e.g., aromatic rings, conjugated systems, heteroatom‑containing functional groups) obtained by grouping atom‑level attributions (see FR‑006 aggregation rule).
2. **Given** the feature importance data, **When** the visualization script runs, **Then** it generates a parity plot (predicted vs. experimental FQY) and a feature importance bar chart that can be saved as an image file.
3. **Given** a molecule with a known high FQY (selected as one of the top‑5 highest FQY values (i.e., the five molecules with the highest experimental FQY in the test set)), **When** the attribution analysis is performed, **Then** at least **3 of the top 5 substructures** must match entries in the curated reference set of fluorophore motifs (see Supplementary Table S1). This constitutes a pass of the interpretability validation.

---

### Edge Cases

- **What happens when** the dataset contains molecules with FQY values of exactly 0 or 1? **How does the system handle** normalization and loss calculation for these boundary values to prevent numerical instability?  
  *Handled by FR‑010 (ε‑clipping of boundary values).*
- **How does the system handle** molecules with rare atom types or bond configurations not seen in the training set during the graph embedding phase?  
  *Handled by FR‑012 (unseen atom/bond logging and safe skipping).*
- **What happens when** the scaffold-based split results in a test set with fewer than 20 molecules, potentially making statistical significance impossible to determine?  
  *Handled by FR‑013 (log a warning; split ratios remain 80/10/10).*

## User Story ID Glossary

- **US-1** – Data Curation and Preprocessing Pipeline (User Story 1)  
- **US-2** – GNN Model Training and Baseline Comparison (User Story 2)  
- **US-3** – Feature Attribution and Interpretability Analysis (User Story 3)

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse SMILES strings into molecular graphs using RDKit, extracting node features (atom type, hybridization, formal charge) and edge features (bond type, conjugation status) for every molecule in the dataset (See US-1).
- **FR-002**: System MUST perform a scaffold‑based split allocating the majority of the data to training, using an 80/10/10 split ([deferred] training, [deferred] validation, [deferred] test), ensuring zero scaffold overlap between the training and test sets to validate generalizability. (See US-1, Constitution Principle VI).
- **FR-003**: System MUST implement a message‑passing GNN with <5 million parameters using PyTorch Geometric, operating in default precision on CPU only (See US-2).
- **FR-004**: System MUST train the model for a maximum of 50 epochs with early stopping (patience=10) based on validation loss, using the Adam optimizer and MSE loss (See US-2).
- **FR-005**: System MUST evaluate both the GNN and a linear regression baseline (using ECFP4 fingerprints) on the test set, reporting R², RMSE, and MAE (See US-2).
- **FR-006**: System MUST apply Integrated Gradients or SHAP to the trained GNN to compute feature importance scores. Atom‑level attributions are **aggregated into chemically meaningful substructures** (e.g., aromatic rings, conjugated fragments, heteroatom‑containing functional groups) detected via RDKit. The system then reports the **top 20 substructures** ranked by summed absolute attribution (See US-3).
- **FR-007**: System MUST generate visualization artifacts including a training convergence plot, a parity plot (predicted vs. experimental), and feature importance charts (See US-3).
- **FR-008**: System MUST execute the entire pipeline (data loading, training, evaluation, interpretation) within a single GitHub Actions job constrained to 2 CPU cores, ~7 GB RAM, and ≤6 hours duration (See US-2).
- **FR-009**: System MUST detect invalid SMILES strings, **exclude** the corresponding molecules from all downstream datasets, and **log** the SMILES and reason for exclusion without terminating the pipeline (See US-1).
- **FR-010**: System MUST use the raw experimental FQY values as regression targets, applying ε‑clipping to the interval [ε, 1‑ε] with ε = 1e‑6 to avoid exact 0/1 instability. No min‑max scaling is performed. (See US-1).
- **FR-011**: System MUST log any occurrences of boundary FQY values (exactly 0 or 1) that are clipped, and include a summary in the final report. (See US-1).
- **FR-012**: System MUST detect atom types or bond configurations not present in the training set; for **new inference inputs** the system logs a warning and **skips** the molecule rather than causing a crash. During evaluation on the held‑out test set, such molecules are retained; a summary report of any test molecules that would be skipped is logged for transparency (See US-1). **Test Scenario**: a synthetic validation set containing a molecule with a lanthanide atom is processed to verify logging and skipping behavior (see FR‑012).
- **FR-013**: System MUST verify the size of the scaffold‑based test set after split; if the test set contains fewer than 20 molecules, the system **logs a warning** indicating limited statistical power but **does not alter** the 80/10/10 split ratios (See US-1).
- **FR-014**: System MUST log the absolute counts of molecules in the training, validation, and test splits, as well as the scaffold overlap statistics, to ensure reproducibility of the data partitioning (See US-1).
- **FR-015**: System MUST record, when available, solvent, temperature, and measurement‑method metadata associated with each experimental FQY value, storing this information alongside the normalized target and using it to assess condition heterogeneity (See US-1).
- **FR-016**: System MUST use a curated reference set of fluorophore motifs (Supplementary Table S1) that is constructed from peer‑reviewed literature sources independent of the training data. The reference set includes diverse motifs, encompassing both aromatic/conjugated fragments **and** non‑conjugated functional groups (e.g., carbonyls, nitro groups). It is stored as `data/reference/fluorophore_motifs.csv` in the repository; its provenance (source articles, DOI list) and selection criteria are documented in `docs/reference_set_readme.md`. **Justification**: an external motif library enables quantitative validation of attribution relevance, which is essential for demonstrating scientific interpretability. (See US-3).
- **FR-018**: System MUST obtain a verified open dataset that contains both SMILES strings and experimental FQY values (FluorDB v1.0,) from a trusted source (`https://huggingface.co/datasets/fluordb/v1`). The dataset files are checksum‑verified before use, ensuring that the data are jointly verified and no separate joining of SMILES‑only and FQY‑only sources is required. **Justification**: using a verified joint dataset satisfies the data‑resource feasibility requirement and ensures reproducibility. (See US-1) (See SC-009).

### Key Entities

- **MoleculeGraph**: Represents a single molecule, containing a set of nodes (atoms) and edges (bonds), with associated features and a scalar FQY target value.
- **DatasetSplit**: A logical grouping of MoleculeGraphs into Train, Validation, and Test sets, defined by unique scaffold identifiers to ensure disjointness.
- **ModelCheckpoint**: A serialized state of the GNN weights and optimizer state, saved at the epoch with the lowest validation loss.
- **AttributionResult**: A data structure mapping specific substructures or atoms to their contribution scores (SHAP/Integrated Gradients values) for a given prediction.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive R² score of the GNN model on the scaffold‑disjoint test set will be **measured** and reported alongside the baseline linear regression R². The magnitude of improvement over baseline will be **described** (e.g., “ΔR² = 0.07”) but no hard pass/fail threshold is imposed (see FR‑005). (See US-1)
- **SC-002**: The total execution time of the end‑to‑end pipeline is measured against the 6‑hour free‑tier CI limit to ensure compute feasibility (See FR‑008). (See US-1)
- **SC-003**: The memory usage peak during model training is measured against the **7 GB RAM limit** to verify the hardware constraint. (See US-1)
- **SC-004**: The consistency of the scaffold split is measured by verifying that the intersection of scaffold identifiers between the training and test sets is exactly zero (See FR‑002). (See US-1)
- **SC-005**: Interpretability is validated by (a) reporting the overlap between the top‑20 substructures (as defined in FR‑006) and the curated reference set of fluorophore motifs (Supplementary Table S1), and (b) comparing this overlap to a random‑baseline distribution generated from 100 draws of 20 substructures. Both the absolute overlap value and the enrichment factor relative to the random baseline will be reported; no fixed numeric gate is imposed. (See US-1)
- **SC-006**: Attribution‑method consistency is assessed by computing the Pearson correlation between Integrated Gradients and SHAP importance scores on **at least 30** randomly selected test molecules. The correlation coefficient will be reported, and a discussion will note whether the two methods agree qualitatively; no hard threshold is required. (See US-1)
- **SC-007**: The pipeline will produce a final report compiling all metrics, logs, and visualizations, and will be archived as an artifact of the GitHub Actions run. (See US-1)
- **SC-008**: The pipeline must log and skip any inference‑time molecule containing atom or bond types unseen during training, and the test scenario described in FR‑012 (processing a synthetic validation set with a lanthanide atom) must be executed to confirm correct logging and skipping behavior. **Ensures robustness of the inference pipeline to out‑of‑distribution chemical space.** (See US-1)
- **SC-009**: The pipeline must verify that every record in the downloaded dataset includes both a valid SMILES string and a corresponding FQY value; the count of such complete records is reported in the final log. (See US-1)

## Assumptions

- **Assumption about data source**: The project assumes that a verified public dataset (FluorDB v1.0,) containing at least 500 molecules with valid SMILES strings and experimental FQY values is available and accessible via a direct URL (`https://huggingface.co/datasets/fluordb/v1`). The dataset files are checksum‑verified before use.
- **Assumption about variable fit**: It is assumed that the selected dataset contains the necessary structural information (atom types, bond types) to derive the required node and edge features; **datasets lacking experimental FQY values are rejected at ingestion with a logged reason**.
- **Assumption about inference framing**: Since the dataset is observational (no random assignment of molecular structures), all findings regarding structure‑property relationships are framed as associational correlations rather than causal effects.
- **Assumption about methodological constraints**: The analysis assumes that a GNN with <5 M parameters and a sampled dataset will fit within the 7 GB RAM and 14 GB disk limits of the free‑tier runner; if the full dataset exceeds this, a stratified sampling strategy will be applied.
- **Assumption about interpretability validity**: The project assumes that Integrated Gradients or SHAP applied to the GNN will yield chemically meaningful attributions that can be mapped back to substructures, provided the model converges.
- **Assumption about threshold justification**: No specific decision cutoffs (e.g., for "high" vs "low" FQY) are introduced in this phase; the model treats FQY as a continuous regression target, avoiding the need for arbitrary classification thresholds and their associated sensitivity analyses.