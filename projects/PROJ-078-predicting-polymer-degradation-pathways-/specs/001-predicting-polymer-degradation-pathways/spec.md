# Feature Specification: Predicting Polymer Degradation Pathways with Graph Neural Networks

**Feature Branch**: `001-polymer-degradation`  
**Created**: 2026-06-13  
**Status**: Draft  
**Input**: User description: "Predicting Polymer Degradation Pathways with Graph Neural Networks"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1)

**As a** computational chemist, **I want** to automatically download, filter, and convert polymer degradation records from NIST Chemistry WebBook and Materials Project into a structured graph dataset, **so that** I have a clean, reproducible foundation for training the model without manual data entry.

**Why this priority**: Without a validated dataset linking SMILES, environmental conditions, and degradation outcomes, no model can be trained or validated. This is the foundational dependency for all subsequent analysis.

**Independent Test**: Can be fully tested by executing the ingestion script against a small subset of known NIST entries and verifying the output CSV contains valid SMILES strings, numeric environmental parameters, and categorical degradation labels.

**Acceptance Scenarios**:

1. **Given** the NIST API returns a record for a polyester with documented hydrolysis products, **When** the ingestion script processes this record, **Then** the output graph object contains the correct SMILES string, temperature/pH/UV values, and a "hydrolysis" degradation label.
2. **Given** a record in the source data lacks a specific environmental condition (e.g., pH is missing), **When** the script processes the record, **Then** the record is either flagged for manual review or imputed with a documented default value (e.g., pH 7, 25°C), and the output log explicitly records the action taken.
3. **Given** the source data contains non-polyester compounds, **When** the script filters the dataset, **Then** only records identified as polyesters (based on functional group detection in SMILES) are retained in the final training set.

---

### User Story 2 - Lightweight GNN Training and Feature Attribution (Priority: P2)

**As a** researcher, **I want** to train a lightweight Graph Neural Network (≤3 layers, hidden dim ≤128) on the prepared dataset and generate feature importance scores via Integrated Gradients, **so that** I can identify which structural motifs correlate with specific degradation pathways.

**Why this priority**: This delivers the core scientific value: mapping structure to mechanism. The lightweight constraint ensures the model runs on the free-tier CI runner (CPU-only), making the research reproducible without expensive hardware.

**Independent Test**: Can be fully tested by running the training script on a fixed random seed, verifying the model converges within 6 hours on a CPU-only runner, and confirming that the Integrated Gradients output highlights specific atoms/bonds in the polymer chain.

**Acceptance Scenarios**:

1. **Given** a training dataset split into [deferred] for training and [deferred] held out, **When** the GNN is trained for 50 epochs using 5-fold cross-validation on the [deferred] split (or leave-one-out if n < 50), **Then** the mean macro-F1 score on the cross-validation folds is reported, and the loss converges within 5% over the last 5 epochs.
2. **Given** a test polymer sample, **When** the model predicts its degradation pathway, **Then** the Integrated Gradients attribution map identifies the ester linkage as a high-importance feature (top [deferred] of attribution scores) for ≥90% of hydrolysis cases, significantly outperforming a null distribution of shuffled motifs.
3. **Given** the training data is augmented via bond rotation and atom masking, **When** the model is retrained, **Then** the validation macro-F1 score improves or remains stable compared to the non-augmented baseline, and the augmentation process completes within 30 minutes.

---

### User Story 3 - Statistical Validation and Motif Reporting (Priority: P3)

**As a** domain expert, **I want** to receive a statistical report confirming that the identified structure-mechanism correlations are significant (via permutation test) and listing the top 3-5 structural motifs, **so that** I can trust the findings are not due to random chance and can use them for polymer design.

**Why this priority**: This transforms the model's output from a "black box" prediction into a scientifically defensible finding, addressing the literature gap regarding data-driven structure-to-pathway mapping.

**Independent Test**: Can be fully tested by running the analysis script on the final model outputs and verifying the generated report contains a p-value from the permutation test and a ranked list of motifs.

**Acceptance Scenarios**:

1. **Given** the model's predictions on the test set, **When** a permutation test is performed by shuffling input motifs 1000 times, **Then** the report includes the calculated p-value comparing the observed motif importance against the permuted null distribution.
2. **Given** the model has identified feature importances, **When** the reporting script aggregates these across the dataset, **Then** the output report lists at least 3 distinct structural motifs (e.g., "aromatic ring proximity to ester bond") with their correlation strength to specific degradation types.
3. **Given** the model identifies a potential degradation pathway, **When** the confidence score is below a defined threshold (e.g., <0.6), **Then** the report flags this prediction as "low confidence" to prevent over-interpretation of uncertain results.

### Edge Cases

- **What happens when** the NIST or Materials Project API rate-limits the requests? **How does the system handle** this? (System MUST implement exponential backoff with a maximum of 3 retries, then fail gracefully with a clear error log).
- **What happens when** the dataset size is too small (<50 instances) to support the 5-fold cross-validation? **How does the system handle** this? (System MUST detect the small sample size and automatically switch to a leave-one-out validation strategy).
- **What happens when** a polymer SMILES string cannot be converted to a valid molecular graph by RDKit? **How does the system handle** this? (System MUST skip the invalid record, log the SMILES string, and continue processing without crashing).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST download polymer degradation records from NIST Chemistry WebBook and Materials Project APIs, filtering specifically for polyesters with documented degradation products (See US-1).
- **FR-002**: System MUST convert polymer SMILES strings to molecular graphs using RDKit, encoding environmental conditions (temperature, pH, UV) as continuous node/edge features, and MUST handle missing values by flagging or imputing with documented defaults (See US-1).
- **FR-003**: System MUST implement a lightweight GNN architecture with ≤3 layers and a hidden dimension ≤128, trained exclusively on CPU without GPU acceleration (See US-2).
- **FR-004**: System MUST apply data augmentation via bond rotation and atom masking to expand the training set by a significant factor within 30 minutes, verifying stability of validation scores (See US-2).
- **FR-005**: System MUST compute feature importance scores using Integrated Gradients to identify structural motifs correlating with degradation pathways (See US-2).
- **FR-006**: System MUST perform a permutation test on input features (shuffling motifs multiple times) to validate the significance of identified structure-mechanism relationships and report the resulting p-value (See US-3).
- **FR-007**: System MUST generate a final report listing the top 3-5 structural motifs and their correlation with specific degradation mechanisms (hydrolysis, photolysis, oxidation) (See US-3).
- **FR-008**: System MUST validate the presence of explicit 'degradation pathway' labels in source data; if missing, it MUST flag the record for manual curation or exclusion (See US-1).

### Key Entities

- **PolymerRecord**: Represents a single entry containing the molecular structure (SMILES), environmental conditions (temperature, pH, UV), and observed degradation pathway.
- **MolecularGraph**: The graph representation of a polymer record, where nodes represent atoms and edges represent bonds, enriched with environmental feature vectors.
- **DegradationPathway**: A categorical label (e.g., "hydrolysis", "oxidation") representing the dominant mechanism observed in the experimental record.
- **MotifImportance**: A derived metric linking a specific subgraph pattern (structural motif) to a predicted degradation pathway with an associated importance score.

## Success Criteria *(mandatory)*

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The prediction performance of the GNN model is measured against the held-out test set and mean cross-validation folds to verify the macro-F1 score target (See US-2).
- **SC-002**: The statistical significance of the structure-mechanism relationship is measured against a permuted null distribution using the permutation test (See US-3).
- **SC-003**: The computational feasibility is measured against the free-tier CI runner constraints (≤6h runtime, ~7GB RAM, CPU-only) to ensure the analysis completes successfully (See US-2).
- **SC-004**: The data coverage is measured against a target of sufficient polymer degradation instances.; if <150, a power analysis warning is triggered (See US-3).
- **SC-005**: The feature attribution validity is measured by verifying that Integrated Gradients identifies ester bonds in the top [deferred] of attribution scores for ≥90% of hydrolysis cases, significantly outperforming a null distribution of shuffled motifs (See US-2).

## Assumptions

- **Assumption about data availability**: The NIST Chemistry WebBook and Materials Project APIs contain sufficient polyester records with documented degradation products to construct a dataset of at least 150 instances; if not, the project scope is limited to available data, and power analysis is triggered for <150 instances.
- **Assumption about environmental variables**: The public records contain explicit or derivable values for temperature, pH, and UV exposure; if a record lacks a specific variable, a community-standard default (e.g., ambient pH 7, 25°C, no UV) will be applied with a flag in the metadata.
- **Assumption about computational resources**: The lightweight GNN (≤3 layers, hidden dim ≤128) and the augmented dataset will fit within the ~7 GB RAM limit of the free-tier GitHub Actions runner; if memory usage exceeds a practical threshold, the dataset will be further subsampled.
- **Assumption about methodological framing**: Since the data is observational (no random assignment), all findings regarding structure-mechanism relationships are framed as associational rather than causal, consistent with the observational nature of the dataset.
- **Assumption about threshold justification**: The [deferred] macro-F1 target and the permutation test methodology are adopted as community-standard defaults for initial exploratory ML studies in chemistry; no sensitivity analysis on these specific thresholds is required for this phase, but the model's performance will be reported across the full validation curve.
- **Assumption about measurement validity**: The degradation pathways labeled in the source datasets are considered ground truth for the purpose of supervised learning, assuming the original experimental methods were valid.