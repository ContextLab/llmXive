# Feature Specification: Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction

**Feature Branch**: `001-comparative-analysis-of-molecular-fingerprints`  
**Created**: 2026-07-08  
**Status**: Draft  
**Input**: User description: "Comparative Analysis of Molecular Fingerprints for Pesticide Toxicity Prediction"

## User Scenarios & Testing

### User Story 1 - Data Acquisition and Organophosphate Filtering (Priority: P1)

The system MUST download the Tox dataset and isolate the specific subset of organophosphate compounds using defined chemical substructure matching.

**Why this priority**: Without a correctly filtered dataset containing only the target chemical class (organophosphates), no comparison of fingerprints is possible. This is the foundational data prerequisite for all subsequent analysis.

**Independent Test**: Can be fully tested by verifying the existence of a filtered CSV file containing only compounds matching the SMARTS pattern `[P](=O)([O,SC])[O,SC]`, with a non-zero row count and valid toxicity labels for the 12 endpoints.

**Acceptance Scenarios**:

1. **Given** the raw Tox21 dataset is available, **When** the system applies the organophosphate SMARTS filter, **Then** the output file contains only compounds with the P=O and P-S/P-O structural motifs.
2. **Given** the filtered dataset, **When** the system validates the toxicity labels, **Then** at least one toxicity endpoint has a non-zero sample count for the filtered subset.

---

### User Story 2 - Fingerprint Generation and Model Training (Priority: P2)

The system MUST generate two distinct feature sets (Morgan fingerprints and MACCS keys) for the filtered compounds and train parallel Random Forest classifiers on a CPU-only environment.

**Why this priority**: This is the core experimental engine. It produces the comparative data required to answer the research question. It must run within the 6-hour CI limit without GPU.

**Independent Test**: Can be fully tested by executing the training script on a sample of compounds to verify functionality, memory safety, and artifact generation. The performance SLA is verified separately against the full filtered dataset during the CI run.

**Acceptance Scenarios**:

1. **Given** the filtered dataset, **When** the system computes fingerprints, **Then** Morgan fingerprints (radius=2, 2048 bits) and MACCS keys are generated without memory errors.
2. **Given** the full filtered dataset (n ≤ 5,000 compounds), **When** the system trains Random Forest models (100 trees, max_depth=15), **Then** the training completes within 60 minutes on a 2-core CPU runner.

---

### User Story 3 - Comparative Evaluation and Statistical Validation (Priority: P3)

The system MUST evaluate both models on a held-out test set, perform a corrected resampled t-test (Nadeau & Bengio) on the test set predictions, and generate a report comparing performance metrics including a bootstrap-derived confidence interval.

**Why this priority**: This delivers the final research insight. It determines if the topological context (Morgan) provides a statistically significant advantage over local substructures (MACCS) for organophosphates using a methodologically sound statistical test.

**Independent Test**: Can be fully tested by running the evaluation script and verifying the output report contains ROC-AUC scores for both models, a p-value from the corrected resampled t-test, and a 95% confidence interval for the performance difference calculated via bootstrapping.

**Acceptance Scenarios**:

1. **Given** the trained models and test set, **When** the system calculates ROC-AUC, **Then** the difference in performance between Morgan and MACCS is reported with a 95% confidence interval derived from 1,000 bootstrap resamples of the paired test-set predictions.
2. **Given** the test set predictions, **When** the system performs a corrected resampled t-test (Nadeau & Bengio), **Then** the output explicitly states whether the performance difference is statistically significant (p < 0.05).

---

### Edge Cases

- **Data Scarcity**: If the filtered organophosphate subset contains fewer than 50 compounds, the system must flag a "Low Sample Size" warning and skip the statistical significance test to avoid Type I errors, recording this limitation in the final report.
- **Label Imbalance**: If a specific toxicity endpoint has a class imbalance ratio > 10:1 (positive:negative), the system must use stratified sampling and report Balanced Accuracy in addition to ROC-AUC.
- **Insufficient Structural Diversity**: If the greedy maximal dissimilarity split algorithm cannot assign a test set of at least 20 samples while maintaining a Tanimoto similarity threshold of < 0.85 against all training samples, the system MUST halt execution, log "Insufficient Structural Diversity: Cannot achieve valid split," and output a report stating that statistical comparison is invalid. The system MUST NOT relax the similarity threshold.
- **Memory Overflow**: If the full dataset exceeds 7 GB of RAM during fingerprint generation, the system MUST switch to a chunked processing mode (batch size = 500 compounds) and log the adjustment, ensuring the final model is trained on the complete dataset.

## Requirements

### Functional Requirements

- **FR-001**: System MUST filter the Tox21 dataset to include only compounds matching the SMARTS pattern `[P](=O)([O,SC])[O,SC]` to isolate organophosphates. (See US-1)
- **FR-002**: System MUST generate Morgan fingerprints (radius=2, 2048 bits) and MACCS keys for every compound in the filtered dataset using RDKit. (See US-2)
- **FR-003**: System MUST train two independent Random Forest classifiers (100 trees, max_depth=15) on the Morgan and MACCS feature sets respectively. (See US-2)
- **FR-004**: System MUST perform a maximal dissimilarity split using a greedy algorithm to ensure NO compound in the test set has a Tanimoto similarity ≥ 0.85 to any compound in the training set, while maintaining an approximate 80/20 split ratio. (See US-2)
- **FR-005**: System MUST execute a corrected resampled t-test (Nadeau & Bengio) on the test set predictions to determine if the performance difference between Morgan and MACCS models is statistically significant (p < 0.05). (See US-3)
- **FR-006**: System MUST enforce a CPU-only execution constraint, prohibiting any GPU/CUDA operations or heavy model training that exceeds available system RAM. (See US-2)

### Key Entities

- **Compound**: A chemical entity represented by its SMILES string, molecular graph, and binary toxicity labels for 12 endpoints.
- **Fingerprint**: A binary vector representation of a compound, either as a 2048-bit Morgan fingerprint or a 166-bit MACCS key.
- **Model**: A trained Random Forest classifier instance associated with a specific fingerprint type and toxicity endpoint.
- **PerformanceMetric**: A quantitative measure (ROC-AUC, Balanced Accuracy) derived from model predictions against ground truth labels.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The difference in ROC-AUC between Morgan and MACCS models is measured against the null hypothesis of no difference (p < 0.05 threshold via corrected resampled t-test). (See FR-005)
- **SC-002**: The computational resource usage (RAM and CPU time) is measured against the GitHub Actions free-tier limits (a standard RAM allocation and runtime duration). (See FR-006)
- **SC-003**: The feature importance distribution is measured against the hypothesis that Morgan bits surrounding the phosphorus center are more predictive. The metric is: The sum of Gini importance for Morgan bits within radius 2 of the phosphorus atom must exceed the sum for MACCS keys by ≥ 15%. (See US-3)
- **SC-004**: The sample size of the organophosphate subset is measured against the minimum viable size for statistical power (n ≥ 50). (See Edge Cases)
- **SC-005**: The Tanimoto similarity distribution between train and test sets is measured against the <0.85 threshold to ensure structural independence. (See FR-004)

## Assumptions

- **Dataset Completeness**: The Tox21 dataset contains sufficient organophosphate compounds (n ≥ 50) to perform a statistically valid comparison; if the count is lower, the study will be limited to descriptive analysis.
- **Instrument Precision**: The toxicity labels in large-scale toxicology datasets are treated as ground truth binary values; measurement uncertainty (standard deviation) is inherent in the assay data and not recalculated, as the assay protocols are fixed by the source.
- **Algorithm Calibration**: The RDKit implementation of Morgan and MACCS fingerprints is assumed to be the industry standard "calibration" for these representations; no external calibration procedure is required beyond standard library usage.
- **Computational Feasibility**: The filtered dataset size will fit within 7 GB of RAM, allowing for in-memory processing of feature generation and model training without disk-swapping.
- **Observational Nature**: The study is purely observational and correlational; no causal claims about molecular structure causing toxicity are made, only associations between fingerprint features and assay outcomes.
- **Threshold Justification**: The Tanimoto similarity threshold of 0.85 is selected based on common cheminformatics practices for scaffold splitting to ensure structural diversity between train and test sets.