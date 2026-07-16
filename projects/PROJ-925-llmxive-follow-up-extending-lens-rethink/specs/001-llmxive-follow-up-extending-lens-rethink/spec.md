# Feature Specification: llmXive follow-up: extending "Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo"

**Feature Branch**: `001-llmxive-lens-extension`  
**Created**: 2026-07-16  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Lens: Rethinking Training Efficiency for Foundational Text-to-Image Mo'"

## User Scenarios & Testing

### User Story 1 - Compute Linguistic Feature Vector for Caption (Priority: P1)

As a data researcher, I want to compute a standardized vector of linguistic features (semantic entropy, syntactic complexity, noun-phrase density) for a given text caption so that I can prepare the data for the deviation prediction model without needing to generate images.

**Why this priority**: This is the foundational data engineering step. Without extracting these specific predictors, the subsequent analysis of the "alignment gap" is impossible. It is the primary input to the entire research pipeline.

**Independent Test**: Can be fully tested by running the feature extraction script on a small, static JSONL file of 10 captions and verifying the output CSV contains the expected numeric columns with no nulls and reasonable ranges.

**Acceptance Scenarios**:

1. **Given** a valid caption string in the input dataset, **When** the feature extraction module processes it, **Then** the output record contains non-null values for semantic entropy, syntactic depth, and noun-phrase density.
2. **Given** a caption with complex nested clauses, **When** processed, **Then** the syntactic complexity metric (dependency tree depth) is strictly higher than that of a simple one-sentence caption.
3. **Given** a caption with repetitive vocabulary, **When** processed, **Then** the token diversity metric is lower than that of a caption with unique vocabulary.

---

### User Story 2 - Calculate Alignment Deviation Score (Priority: P2)

As a researcher, I want to calculate the "alignment deviation" score for each sample by taking the absolute difference between the pre-computed CLIP score and the human rating, so that I have a precise target variable representing the metric failure.

**Why this priority**: This defines the "Y" variable for the regression/classification task. It isolates the specific phenomenon (the gap) the research aims to explain. It must be computed independently of the linguistic features to ensure non-circularity.

**Independent Test**: Can be fully tested by feeding a dataset where the CLIP score and Human Rating are manually known, verifying the script calculates the absolute difference correctly and handles missing human ratings by excluding the row.

**Acceptance Scenarios**:

1. **Given** a sample with a CLIP score of 0.85 and a human rating of 0.90, **When** the deviation module runs, **Then** the output deviation score is exactly 0.05.
2. **Given** a sample where the human rating is missing (NaN), **When** the module runs, **Then** that sample is excluded from the training set rather than causing a crash or imputation.
3. **Given** the full dataset, **When** processed, **Then** the distribution of deviation scores is stored in a separate column distinct from the input features to prevent data leakage.

---

### User Story 3 - Train CPU-Only Predictor and Rank Features (Priority: P3)

As a researcher, I want to train a Gradient Boosted Trees model (XGBoost) on a CPU-only environment to predict the alignment deviation using only the linguistic features, and output a ranked list of feature importances, so that I can identify which linguistic mechanisms drive the metric failure.

**Why this priority**: This delivers the core research finding (the answer to the research question). It validates the hypothesis that linguistic complexity predicts the gap. It must run within the strict CPU constraints to be feasible.

**Independent Test**: Can be fully tested by executing the training script on a local CPU environment with a subset of the data, verifying that the model converges, produces a correlation score > 0.0, and outputs a JSON file listing feature importances.

**Acceptance Scenarios**:

1. **Given** the feature matrix and target vector, **When** the training script runs on a 2-core CPU, **Then** the job completes within 6 hours and consumes less than 7 GB of RAM.
2. **Given** the trained model, **When** evaluated on a held-out test set, **Then** the Pearson correlation between predicted and actual deviation is reported in the results log.
3. **Given** the final model, **When** permutation importance is calculated, **Then** the output ranks semantic entropy and syntactic complexity as the top predictors if the hypothesis holds.

---

### Edge Cases

- What happens when the dataset contains captions that are too short to compute a meaningful dependency tree depth (e.g., single words)? The system must handle this by assigning a default minimum depth or excluding the sample, logging the exclusion reason.
- How does the system handle a scenario where the human rating and CLIP score are identical for all samples (zero variance in target)? The system must detect zero variance in the target variable and halt training with a specific error message indicating the target is not learnable.
- How does the system handle missing values in the linguistic feature extraction (e.g., BERT perplexity fails)? The system must catch the exception, log the specific caption ID, and exclude that row from the final training matrix.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST compute semantic entropy for each caption using a pre-trained BERT-based perplexity model, where semantic entropy is defined as the natural logarithm of the perplexity value (entropy = ln(perplexity)). The calculation MUST complete within 5 seconds per caption on a standard CPU. (See US-1)
- **FR-002**: The system MUST calculate syntactic complexity by determining the maximum depth of the dependency parse tree for each caption, using a deterministic parser like spaCy. (See US-1)
- **FR-003**: The system MUST derive the target variable as the absolute difference $| \text{CLIP\_Score} - \text{Human\_Rating} |$. Before calculation, the system MUST normalize both the CLIP score and the Human Rating to the [0, 1] range to ensure mathematical validity. Samples where the human rating is missing MUST be excluded. (See US-2)
- **FR-004**: The system MUST train a Gradient Boosted Trees model (e.g., XGBoost) using only CPU resources, strictly avoiding any GPU acceleration, CUDA dependencies, or mixed-precision training modes. (See US-3)
- **FR-005**: The system MUST perform a permutation importance analysis on the trained model to rank linguistic features by their contribution to predicting the alignment deviation. (See US-3)
- **FR-006**: The system MUST perform a permutation-based significance test for feature importance by generating a null distribution via label permutation (at least 1,000 iterations), calculating p-values against this null, and applying the Benjamini-Hochberg procedure to control the false discovery rate at 0.05. The specific method (Benjamini-Hochberg) and random seed MUST be logged and pinned in the code to ensure reproducibility. (See US-3)

### Key Entities

- **CaptionRecord**: Represents a single data point containing the raw text, computed linguistic features, CLIP score, human rating, and the derived deviation score.
- **LinguisticFeatureVector**: A structured set of numerical values (entropy, depth, density, diversity) extracted from a caption, serving as the predictor set ($X$).
- **DeviationScore**: A single floating-point value representing the magnitude of the gap between algorithmic and human judgment, serving as the target ($Y$).
- **FeatureImportanceRanking**: A sorted list of linguistic features ordered by their predictive power for the deviation score, derived from the trained model.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation phase.

- **SC-001**: The Pearson correlation coefficient between the model's predicted deviation and the actual deviation is measured against a baseline of zero (no predictive power) to confirm the model explains variance. (See US-3)
- **SC-002**: The memory footprint of the training process is measured against the RAM limit of the free-tier CI runner to ensure feasibility. (See US-3)
- **SC-003**: The total wall-clock time for the end-to-end pipeline (feature extraction + training + evaluation) is measured against the job limit of the CI runner. (See US-3)
- **SC-004**: The statistical significance of the top-ranked linguistic features is measured against a corrected p-value threshold of p < 0.05 (after Benjamini-Hochberg correction) to validate the findings. (See US-3)
- **SC-005**: The sensitivity of the feature importance rankings is measured against a sweep of random seeds (e.g., multiple seeds) to ensure the results are robust and not artifacts of a specific initialization. (See US-3)

## Assumptions

- **Assumption about data availability**: The COCO Captions dataset or a HuggingFace-hosted subset containing both image captions and associated human preference ratings (e.g., from Pick-a-Pic) is publicly accessible and fits within the disk limit of the CI runner.
- **Assumption about computational constraints**: The linguistic feature extraction (BERT perplexity) can be performed on a CPU within a fixed time budget for the chosen dataset size (likely a subset of tens of thousands of samples); if the full dataset is too large, the analysis will operate on a stratified random sample.
- **Assumption about inference framing**: Since the design is observational (using existing dataset pairs without random assignment), all conclusions regarding the relationship between linguistic features and alignment deviation will be framed as associational, not causal.
- **Assumption about measurement validity**: The "semantic entropy" metric derived from BERT perplexity (defined as ln(perplexity)) is used as an operational proxy for linguistic/semantic uncertainty in this study, acknowledging it differs from the strict semantic entropy definition (Farquhar et al., 2024) but serves as a computable indicator of model uncertainty.
- **Assumption about threshold justification**: No arbitrary classification thresholds are introduced; the analysis relies on continuous regression metrics (MSE, Pearson correlation) which do not require decision cutoffs, thereby avoiding the need for sensitivity analysis on thresholds.
- **Assumption about target noise**: The human rating is treated as the ground truth for the purpose of calculating the deviation score, despite the known risk of "noise-as-signal" where human rating variance may obscure the true alignment gap. The robustness of findings to this noise will be assessed via the sensitivity analysis in SC-005.