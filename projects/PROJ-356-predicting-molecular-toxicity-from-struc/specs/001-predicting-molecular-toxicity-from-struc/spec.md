# Feature Specification: Predicting Molecular Toxicity from Structural Alerts via Rule-Based Systems

**Feature Branch**: `001-predicting-molecular-toxicity`  
**Created**: 2026-06-13  
**Status**: Draft  
**Input**: User description: "Predicting Molecular Toxicity from Structural Alerts via Rule-Based Systems"

## User Scenarios & Testing

### User Story 1 - Reproducible Baseline Comparison (Priority: P1)

A researcher needs to download a public mutagenicity dataset (PubChem/ToxCast), compute two distinct feature sets (rule-based structural alerts and global molecular descriptors), and train two baseline models (rule-based scoring and Logistic Regression) to compare their predictive performance on a held-out test set.

**Why this priority**: This is the core scientific validation. Without a reproducible pipeline that generates both feature sets and compares them, the research question cannot be answered. It establishes the baseline performance gap between interpretability (rules) and holistic modeling (descriptors).

**Independent Test**: The pipeline can be fully tested by running the data acquisition, feature extraction, and model training scripts on a local CPU environment and verifying that the script outputs a JSON report containing ROC-AUC and F1 scores for both models without requiring external API calls or GPU resources.

**Acceptance Scenarios**:

1. **Given** a valid list of PubChem BioAssay IDs, **When** the data acquisition script runs, **Then** it successfully downloads SMILES strings and binary mutagenicity labels (active/inactive) and saves them to a local CSV file.
2. **Given** a standardized SMILES file, **When** the feature extraction module runs, **Then** it outputs two parallel datasets: one containing binary vectors for SMARTS pattern matches and another containing continuous global molecular descriptors.
3. **Given** the extracted feature datasets, **When** the training script executes with a 5-fold stratified cross-validation repeated 3 times, **Then** it trains a rule-based scorer and a Logistic Regression model, saves both to disk, and generates a summary report with ROC-AUC values for the test set.

---

### User Story 2 - Statistical Significance Verification (Priority: P2)

A researcher needs to determine if the performance difference between the rule-based model and the descriptor-based model is statistically significant rather than due to random sampling variance, using DeLong's test.

**Why this priority**: A difference in AUC is meaningless without a statistical test. This step ensures the conclusions drawn about "marginal gain" are scientifically defensible and not artifacts of noise, addressing the reviewer's concern for rigorous quantification.

**Independent Test**: The statistical analysis module can be tested by providing it with two vectors of predicted probabilities from the models (averaged across CV folds per instance) and verifying that it outputs a p-value and confidence interval indicating whether the AUC difference is significant at the 0.05 level.

**Acceptance Scenarios**:

1. **Given** the predicted probabilities from the rule-based and descriptor-based models on the same test set (averaged per instance across 15 folds), **When** the statistical analysis script runs, **Then** it performs DeLong's test and outputs a p-value.
2. **Given** a p-value < 0.05, **When** the report is generated, **Then** it explicitly flags the result as "statistically significant" and recommends the superior model.
3. **Given** a p-value ≥ 0.05, **When** the report is generated, **Then** it flags the result as "no significant difference" and suggests that the added complexity of descriptors may not be justified for this dataset.

---

### User Story 3 - Error Analysis and Alert Gap Identification (Priority: P3)

A researcher needs to inspect the false negatives of the rule-based model to identify specific chemical classes where the curated structural alerts failed to predict mutagenicity, enabling hypothesis generation for missing alerts.

**Why this priority**: This provides the "interpretability" value proposition. If the rule-based model fails, the researcher must know *why* (e.g., missing a specific nitro-aryl pattern) to improve the rule set or justify the need for complex models.

**Independent Test**: The error analysis module can be tested by feeding it the test set predictions and labels, filtering for false negatives, and verifying that it outputs a list of unique chemical substructures or scaffold classes associated with these failures.

**Acceptance Scenarios**:

1. **Given** the test set predictions and ground truth labels, **When** the error analysis script runs, **Then** it isolates all compounds classified as "inactive" by the rule-based model but "active" in the assay.
2. **Given** the false negative compounds, **When** the substructure analysis runs, **Then** it generates a frequency distribution of the top 10 missing or weak structural motifs present in these compounds using Murcko scaffolds.
3. **Given** the identified motifs, **When** the report is generated, **Then** it lists specific chemical classes (e.g., "sulfonamides," "epoxides") that require new SMARTS patterns to improve recall.

---

### Edge Cases

- What happens when the downloaded dataset contains duplicate SMILES strings with conflicting activity labels? The system must deduplicate based on canonical SMILES and flag or discard conflicting entries, logging the count of removed duplicates.
- How does the system handle molecules that exceed the 1000 Da mass limit or contain non-standard elements? These molecules must be filtered out during preprocessing, and a count of excluded molecules must be reported.
- What happens if a SMARTS pattern fails to compile due to syntax errors? The system must catch the exception, log the specific pattern string, skip it, and continue processing without crashing the entire pipeline.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download mutagenicity assay data (SMILES and binary labels) from PubChem BioAssay (specific assay identifiers) and/or ToxCast and save it to a local CSV file (See US-1).
- **FR-002**: The system MUST standardize input SMILES strings using RDKit and filter for molecules with a molecular weight < 1000 Da (See US-1).
- **FR-003**: The system MUST generate a binary feature vector for each molecule based on the presence of at least 10 curated SMARTS patterns loaded from `config/structural_alerts.json`, which must contain specific toxicophores (e.g., nitroaromatics, epoxides, primary aromatic amines) (See US-1).
- **FR-004**: The system MUST compute at least 20 global molecular descriptors (specifically the first 20 non-correlated descriptors from the RDKit `rdkit.Chem.Descriptors` module) for each molecule (See US-1).
- **FR-005**: The system MUST train a rule-based scoring model (sum of alert weights loaded from `config/structural_alerts.json`, defaulting to 1.0 if undefined) and a Logistic Regression model using a 5-fold stratified cross-validation repeated 3 times (See US-1).
- **FR-006**: The system MUST evaluate both models using ROC-AUC and F1-score metrics on the held-out test set (See US-1).
- **FR-007**: The system MUST perform DeLong's test to compare the AUC of the rule-based and descriptor-based models using predictions averaged per instance across all CV folds, outputting a p-value (See US-2).
- **FR-008**: The system MUST identify and list the top unique Murcko scaffolds present in the false negatives of the rule-based model. (See US-3).
- **FR-009**: The system MUST NOT apply multiple-comparison correction as only a single primary hypothesis test (DeLong's test) is performed (See US-2).
- **FR-010**: The system MUST execute the entire pipeline on a CPU-only environment with a maximum runtime of a reasonable duration and memory usage under 7 GB (See Assumptions).

### Key Entities

- **Molecule**: Represents a chemical entity with attributes: `canonical_smiles`, `molecular_weight`, `mutagenicity_label` (binary), `structural_alerts` (binary vector), `global_descriptors` (float vector).
- **StructuralAlert**: Represents a specific toxicophore defined by a SMARTS pattern, with attributes: `pattern_id`, `smarts_string`, `weight`, `description`.
- **ModelResult**: Represents the outcome of a model evaluation, with attributes: `model_type`, `roc_auc`, `f1_score`, `confusion_matrix`.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The difference in ROC-AUC between the rule-based and descriptor-based models is measured against the statistical significance threshold (p < 0.05) determined by DeLong's test (See US-2).
- **SC-002**: The difference in recall between the descriptor-based model and the rule-based model is measured against a threshold of 5% to quantify the "marginal gain" (See US-1).
- **SC-003**: The number of false negatives in the rule-based model is measured against the count of identified missing structural motifs to determine the feasibility of rule-set expansion (See US-3).
- **SC-004**: The total runtime of the analysis pipeline is measured against a predefined feasibility threshold to ensure compatibility with free-tier CI runners. (See Assumptions).
- **SC-005**: The memory footprint of the feature extraction and model training steps is measured against the system's RAM limit to ensure no out-of-memory errors occur. (See Assumptions).

## Assumptions

- The PubChem BioAssay AID 1851 or ToxCast dataset contains sufficient samples (N > 1000) with both SMILES strings and binary mutagenicity labels to support a meaningful 5-fold stratified cross-validation repeated 3 times.
- The `rdkit` and `scikit-learn` Python libraries are available and compatible with the CPU-only GitHub Actions runner environment.
- The curated SMARTS patterns for structural alerts (e.g., nitroaromatics, epoxides) are sufficient to cover the majority of high-severity mutagenicity cases in the dataset, as per existing toxicological literature.
- The dataset does not contain significant class imbalance that would render standard Logistic Regression ineffective without resampling; stratified cross-validation inherently handles class imbalance by preserving label distribution in every fold.
- The analysis will be performed on a sampled subset of the data if the full dataset exceeds available memory capacity, ensuring the compute feasibility constraint is met.
- The "structural alerts" are treated as independent predictors in the rule-based model, and their weights are summed linearly without interaction terms. This linear sum model is structurally incapable of modeling interaction effects (synergy/antagonism) between toxicophores, which is treated as a known confounding variable in the comparison with global descriptors.
- The dataset variable fit is confirmed: the source data contains the necessary structural information (SMILES) to derive both structural alerts and global descriptors, and the outcome variable (mutagenicity) is independent of the structural derivation.
- The inference framing is strictly associational; no causal claims will be made regarding the effect of specific structural motifs on mutagenicity, only their predictive correlation.
- Any decision thresholds (e.g., probability cutoff for classification) used in error analysis will be swept over a small set (e.g., 0.3, 0.5, 0.7) to ensure sensitivity, with the 0.5 default used for primary reporting.
- The power of the statistical test (DeLong's) is sufficient for the sample size; if the sample size is small, the limitation will be explicitly noted in the final report.
- The weights for structural alerts are pre-curated constants from literature, ensuring the rule-based model is a fixed heuristic and the comparison to Logistic Regression is non-trivial.