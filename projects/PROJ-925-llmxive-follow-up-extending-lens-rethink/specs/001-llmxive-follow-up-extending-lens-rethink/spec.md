# Feature Specification: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

**Feature Branch**: `001-llmxive-lens-extension`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo'"

## User Scenarios & Testing

### User Story 1 - Compute Linguistic Feature Vector for Caption (Priority: P1)

As a data researcher, I want to compute a standardized vector of linguistic features (linguistic uncertainty proxy, syntactic complexity, noun-phrase density) for a given text caption so that I can prepare the data for the deviation prediction model without needing to generate images.

**Why this priority**: This is the foundational data engineering step. Without extracting these specific predictors, the subsequent analysis of the "alignment gap" is impossible. It is the primary input to the entire research pipeline.

**Independent Test**: Can be fully tested by running the feature extraction script on a small, static JSONL file of 10 captions and verifying the output CSV contains the expected numeric columns with no nulls and reasonable ranges.

**Acceptance Scenarios**:

1. **Given** a valid caption string in the input dataset, **When** the feature extraction module processes it, **Then** the output record contains non-null values for linguistic uncertainty proxy, syntactic depth, and noun-phrase density.
2. **Given** a caption with complex nested clauses, **When** processed, **Then** the syntactic complexity metric (dependency tree depth) is strictly higher than that of a simple one-sentence caption.
3. **Given** a caption with repetitive vocabulary, **When** processed, **Then** the token diversity metric is lower than that of a caption with unique vocabulary.

---

### User Story 2 - Calculate Alignment Deviation Score (Priority: P2)

As a researcher, I want to calculate the "alignment deviation" score for each sample by taking the absolute difference between the pre-computed CLIP score and the human preference rating from the 'pick-a-pic' dataset, so that I have a precise target variable representing the metric failure.

**Why this priority**: This defines the "Y" variable for the regression/classification task. It isolates the specific phenomenon (the gap) the research aims to explain. It must be computed independently of the linguistic features to ensure non-circularity.

**Independent Test**: Can be fully tested by feeding a dataset where the CLIP score and Human Rating are manually known, verifying the script calculates the absolute difference correctly and handles missing human ratings by raising a `DataSchemaError`.

**Acceptance Scenarios**:

1. **Given** a sample with a CLIP score of 0.85 and a human rating of 0.90, **When** the deviation module runs, **Then** the output deviation score is exactly 0.05.
2. **Given** a sample where the human rating is missing (NaN), **When** the module runs, **Then** that sample is excluded from the training set rather than causing a crash or imputation.
3. **Given** the full dataset, **When** processed, **Then** the distribution of deviation scores is stored in a separate column distinct from the input features to prevent data leakage.

---

### User Story 3 - Train CPU-Only Predictor and Rank Features (Priority: P3)

As a researcher, I want to train a Gradient Boosted Trees model (XGBoost) on a standard CPU environment to predict the alignment deviation using only the linguistic features, and output a ranked list of feature importances, so that I can identify which linguistic mechanisms drive the metric failure.

**Why this priority**: This delivers the core research finding (the answer to the research question). It validates the hypothesis that linguistic complexity predicts the gap. It must run within the strict CPU constraints to be feasible.

**Independent Test**: Can be fully tested by executing the training script on a local CPU environment with a subset of the data, verifying that the model converges, produces a correlation score > 0.0, and outputs a JSON file listing feature importances.

**Acceptance Scenarios**:

1. **Given** the feature matrix and target vector, **When** the training script runs on a standard CPU, **Then** the job completes within 6 hours and consumes less than 7 GB of RAM.
2. **Given** the trained model, **When** evaluated on a held-out test set, **Then** the Pearson correlation between predicted and actual deviation is reported in the results log.
3. **Given** the final model, **When** permutation importance is calculated, **Then** the output ranks linguistic uncertainty proxy and syntactic complexity as the top predictors if the hypothesis holds.

---

### Edge Cases

- What happens when the dataset contains captions that are too short to compute a meaningful dependency tree depth (e.g., single words)? The system must handle this by excluding the sample from the training matrix and logging the exclusion reason with the specific caption ID. (See FR-011)
- How does the system handle a scenario where the human rating and CLIP score are identical for all samples (zero variance in target)? The system must detect zero variance in the target variable and halt training with a specific error message indicating the target is not learnable. (See FR-010)
- How does the system handle missing values in the linguistic feature extraction (e.g., BERT perplexity fails)? The system must catch the exception, log the specific caption ID, and exclude that row from the final training matrix. (See FR-012)

## Requirements

### Functional Requirements

- **FR-001**: The system MUST compute a "Linguistic Uncertainty Proxy" for each caption using a pre-trained BERT-based perplexity model, where the proxy is defined as the natural logarithm of the perplexity value (proxy = ln(perplexity)). This metric serves as an operational proxy for semantic uncertainty in the context of image generation alignment, subject to validation per FR-009. The calculation MUST complete within 5 seconds per caption on a standard CPU. (See US-1)
- **FR-002**: The system MUST calculate syntactic complexity by determining the maximum depth of the dependency parse tree for each caption, using a deterministic parser like spaCy. (See US-1)
- **FR-003**: The system MUST derive the target variable as the absolute difference $| \text{CLIP\_Score} - \text{Human\_Rating} |$ using data from the 'pick-a-pic' dataset. Before calculation, the system MUST standardize both the CLIP score and the Human Rating using Z-score normalization (subtract mean, divide by standard deviation) to ensure mathematical validity and account for distributional shifts. Samples where the human rating is missing MUST be excluded. If the 'pick-a-pic' dataset is unavailable or the 'human_rating' column is absent, the system MUST raise a `DataSchemaError` with the message "Missing required dataset or column: pick-a-pic/human_rating" and halt execution. No synthetic or fallback data sources are permitted. (See US-2)
- **FR-004**: The system MUST train a Gradient Boosted Trees model (e.g., XGBoost) using only CPU resources, strictly avoiding any GPU acceleration, CUDA dependencies, or mixed-precision training modes. (See US-3)
- **FR-005**: The system MUST perform a permutation importance analysis on the trained model to rank linguistic features by their contribution to predicting the alignment deviation. (See US-3)
- **FR-006**: The system MUST perform a permutation-based significance test for feature importance by shuffling the input features (X) to generate a null distribution (N_permutations = 1,000 by default), calculating p-values against this null, and applying the Benjamini-Hochberg procedure to control the false discovery rate at a conventional threshold (FDR ≤ 0.05). The specific method (Benjamini-Hochberg), random seed, and iteration count MUST be logged and pinned in the code to ensure reproducibility. The system MUST also perform a sensitivity analysis by sweeping the significance threshold over a range of conventional levels (e.g., 0.01, 0.05, 0.1) and output a JSON table containing the mean rank and standard deviation of each feature's importance across the sweeps. (See US-3)
- **FR-007**: The system MUST control for confounds by including caption length (number of tokens) and textual description complexity (defined strictly as the count of distinct noun phrases or named entities in the caption, derived solely from text) as covariates in the regression model to rule out spurious correlations. Image data MUST NOT be used for this covariate. (See US-3)
- **FR-008**: The system MUST perform a sensitivity analysis on the human rating noise by injecting synthetic noise (Gaussian noise with varying standard deviations) into the human ratings and re-running the regression to assess the robustness of feature importance rankings. (See US-3)
- **FR-009**: The system MUST validate the "Linguistic Uncertainty Proxy" (ln(perplexity)) by computing its correlation with a semantic entropy baseline or expert annotation on a held-out subset of captions. If the correlation coefficient is < 0.3, the system MUST log a warning and flag the construct validity risk in the final report. (See US-1)
- **FR-010**: The system MUST detect zero variance in the target variable (deviation score) before training and halt with the error message "Target not learnable: zero variance detected". (See US-2)
- **FR-011**: The system MUST handle captions that are too short to compute a meaningful dependency tree depth by excluding the sample from the training matrix and logging the exclusion reason with the specific caption ID. (See US-1)
- **FR-012**: The system MUST handle missing values in the linguistic feature extraction (e.g., BERT perplexity failure) by catching the exception, logging the specific caption ID, and excluding that row from the final training matrix. (See US-1)

### Constitution Enforcement

To ensure compliance with Constitution Principle VI (Linguistic Feature Isolation) and Principle VII (CPU-Tractability), the system MUST enforce the following code-level constraints:
- **CPU-Only Enforcement**: The `train.py` script MUST explicitly set `torch.set_num_threads(1)` and `torch.set_num_interop_threads(1)` at startup. Any import of `torch.cuda` or `tensorflow` with GPU devices MUST raise an `ImportError` if detected.
- **Feature Isolation Enforcement**: The `features.py` script MUST NOT import any image processing libraries (e.g., `PIL`, `opencv`) or CLIP models. It MUST only import text-processing libraries (e.g., `spaCy`, `transformers`). Note: Covariates defined in FR-007 (textual description complexity) MUST be derived using text-only methods.
- **Verification**: These enforcement rules MUST be verified via automated static analysis tests in `code/tests/test_constitution.py`, which assert that no forbidden imports exist in the specified modules.

### Key Entities

- **CaptionRecord**: Represents a single data point containing the raw text, computed linguistic features, CLIP score, human rating, and the derived deviation score.
- **LinguisticFeatureVector**: A structured set of numerical values (entropy, depth, density, diversity) extracted from a caption, serving as the predictor set ($X$).
- **DeviationScore**: A single floating-point value representing the magnitude of the gap between algorithmic and human judgment, serving as the target ($Y$).
- **FeatureImportanceRanking**: A sorted list of objects (JSON array), where each object contains:
  - `feature_name` (string): The name of the linguistic feature.
  - `importance_score` (float): The mean decrease in performance when this feature is shuffled.
  - `p_value` (float): The adjusted p-value from the permutation test.
  - `mean_rank` (float): The mean rank across sensitivity sweeps (if applicable).
  - `std_dev_rank` (float): The standard deviation of rank across sensitivity sweeps (if applicable).

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The Pearson correlation coefficient between the model's predicted deviation and the actual deviation is measured against a threshold of $r \ge 0.1$ with $p < 0.05$ to confirm the model explains variance. (See US-3)
- **SC-002**: The memory footprint of the training process is measured against the 7 GB RAM limit defined in US-3. (See US-3)
- **SC-003**: The total wall-clock time for the end-to-end pipeline (feature extraction + training + evaluation) is measured against the 6-hour CPU budget defined in US-3. (See US-3)
- **SC-004**: The statistical significance of the top-ranked linguistic features is measured against a corrected p-value threshold of $p < 0.05$ (after Benjamini-Hochberg correction) to validate the findings. (See US-3)
- **SC-005**: The sensitivity of the feature importance rankings is measured against a sweep of random seeds (specifically, iterating over multiple seeds, retraining, and aggregating mean rank and standard deviation) to ensure the results are robust and not artifacts of a specific initialization. (See US-3)

## Assumptions

- **Assumption about data availability**: The analysis relies exclusively on the 'pick-a-pic' dataset (or a verified HuggingFace subset) which contains explicit human preference ratings. Standard COCO datasets do not contain these ratings. If 'pick-a-pic' is unavailable, the system MUST halt (FR-003); no synthetic fallbacks are permitted.
- **Assumption about computational constraints**: The linguistic feature extraction (BERT perplexity) can be performed on a CPU within a fixed time budget for the chosen dataset size; if the full dataset is too large, the analysis will operate on the full dataset or a verified subset, failing loudly if data is insufficient.
- **Assumption about inference framing**: Since the design is observational (using existing dataset pairs without random assignment), all conclusions regarding the relationship between linguistic features and alignment deviation will be framed as associational, not causal.
- **Assumption about measurement validity**: The "Linguistic Uncertainty Proxy" metric derived from BERT perplexity (defined as ln(perplexity)) is used as an operational proxy for linguistic/semantic uncertainty in this study, subject to validation per FR-009.
- **Assumption about threshold justification**: No arbitrary classification thresholds are introduced; the analysis relies on continuous regression metrics (MSE, Pearson correlation) which do not require decision cutoffs, thereby avoiding the need for sensitivity analysis on thresholds (except for the significance threshold sweep in FR-006).
- **Assumption about target noise**: The human rating is treated as the ground truth for the purpose of calculating the deviation score, despite the known risk of "noise-as-signal" where human rating variance may obscure the true alignment gap. The robustness of findings to this noise will be assessed via the sensitivity analysis in FR-008.
- **Assumption about project structure**: Schema definitions for data contracts reside in `specs/001-llmxive-follow-up-extending-lens-rethink/contracts/`, while the corresponding validation tests reside in `code/tests/contract/`. The `code/tests/contract/` directory contains unit tests for the schemas defined in the specs.

## Limitations

- The target variable $Y$ conflates 'model error' (CLIP deviation) with 'human subjectivity' (noise in human ratings). The study acknowledges that without a ground-truth 'reality' score, the model predicts 'how much CLIP disagrees with noisy human labels,' not the true alignment gap. This conflation is addressed by the sensitivity analysis in FR-008.
- The study design is purely observational. While confounds are controlled for (FR-007), unmeasured confounds may still exist.

## Constitution Check

- **Principle VI (Linguistic Feature Isolation)**: PASS. Enforced via explicit import restrictions in `features.py` and automated tests in `code/tests/test_constitution.py` (see Constitution Enforcement).
- **Principle VII (CPU-Tractability)**: PASS. Enforced via explicit thread settings and GPU import guards in `train.py` and automated tests in `code/tests/test_constitution.py` (see Constitution Enforcement).