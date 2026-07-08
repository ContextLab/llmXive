# Data Model: Predicting Molecular Toxicity from Structural Alerts via Rule-Based Systems

## Entity Definitions

### Molecule
Represents a single chemical entity in the dataset.
-   `canonical_smiles` (string): Standardized SMILES string (RDKit canonicalization).
-   `molecular_weight` (float): Molecular weight in Daltons.
-   `mutagenicity_label` (int): Binary label (1 = Active/Mutagenic, 0 = Inactive).
-   `structural_alerts` (list[bool]): Binary vector of length K (K=10+) indicating presence of alerts.
-   `global_descriptors` (list[float]): Vector of molecular descriptors (fixed set) with a dimensionality determined by the chosen descriptor set.
-   `murcko_scaffold` (string): Canonicalized Murcko scaffold SMILES (for error analysis).

### StructuralAlert
Represents a curated toxicophore rule.
-   `pattern_id` (string): Unique identifier (e.g., "ALERT_001").
-   `smarts_string` (string): The SMARTS pattern definition.
-   `weight` (float): Contribution weight to the rule-based score (default 1.0).
-   `description` (string): Human-readable description of the toxicophore.

### ModelResult
Represents the evaluation outcome of a model.
-   `model_type` (string): "rule_based" or "logistic_regression".
-   `roc_auc` (float): Area Under the ROC Curve (calculated via continuous threshold sweep).
-   `f1_score` (float): Harmonic mean of precision and recall.
-   `recall` (float): Recall metric.
-   `confusion_matrix` (dict): Keys: "TP", "FP", "TN", "FN".
-   `predictions` (list[float]): Predicted probabilities for the test set (OOF).

### StatisticalTestResult
Represents the outcome of the model comparison.
-   `test_name` (string): "DeLong's Test".
-   `p_value` (float): Probability value.
-   `significant` (bool): True if p_value < 0.05.
-   `ci_lower` (float): Lower bound of 95% CI.
-   `ci_upper` (float): Upper bound of 95% CI.

### RecallComparison
Represents the recall difference metric.
-   `rule_recall` (float): Recall of the rule-based model.
-   `descriptor_recall` (float): Recall of the descriptor-based model.
-   `difference` (float): Descriptor Recall - Rule Recall.
-   `exceeds_threshold` (bool): True if difference > 0.05.

### ErrorAnalysisResult
Represents the false negative analysis.
-   `false_negative_count` (int): Total number of false negatives.
-   `unique_motif_count` (int): Number of unique scaffolds in false negatives.
-   `top_scaffolds` (list[string]): Top 10 unique Murcko scaffolds.
-   `feasibility_note` (string): Text describing the feasibility of rule-set expansion based on counts.

## Data Flow

1.  **Raw Data**: Downloaded CSV (SMILES, Label).
2.  **Preprocessed Data**: Standardized SMILES, filtered by MW < 1000 Da.
3.  **Feature Data**:
    -   `features_alerts.csv`: `canonical_smiles`, `label`, `alert_1`...`alert_K`.
    -   `features_descriptors.csv`: `canonical_smiles`, `label`, `desc_1`...`desc_20`.
4.  **Model Artifacts**: Pickled models, prediction JSONs.
5.  **Report**: JSON summary of metrics, statistical test, recall comparison, and error analysis.

## Constraints & Validation

-   **SMILES**: Must be valid RDKit Mol objects.
-   **MW**: Must be < 1000 Da.
-   **Label**: Must be 0 or 1.
-   **Descriptors**: Must be numeric; NaNs imputed with median.
-   **Alerts**: Must be binary (0/1).
-   **Descriptor Set**: Must be exactly the pre-defined descriptors (no data-dependent selection).