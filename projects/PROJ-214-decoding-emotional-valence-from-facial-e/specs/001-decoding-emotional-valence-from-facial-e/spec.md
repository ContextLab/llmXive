# Feature Specification: Decoding Emotional Valence from Facial EMG Patterns with Machine Learning

**Feature Branch**: `001-decoding-emotional-valence-from-facial-emg`
**Created**: 2026-06-24
**Status**: Draft
**Input**: User description: "Decoding Emotional Valence from Facial EMG Patterns with Machine Learning"

## User Scenarios & Testing

### User Story 1 - Core Valence Classification Pipeline (Priority: P1)

The system must ingest the DEAP dataset, preprocess facial EMG signals (corrugator, zygomaticus, orbicularis) using standard filtering and windowing, extract time-domain features (RMS, ZCR, WAMP, MAV), and train a binary classifier to distinguish positive vs. negative valence.

**Why this priority**: This is the foundational scientific contribution. Without a working pipeline that transforms raw signals into a valid classification model, no further analysis (feature importance, variance explanation) is possible. It validates the core hypothesis that EMG patterns contain valence information.

**Independent Test**: Can be fully tested by running the preprocessing and training script on a subset of subjects and verifying that the cross-validated accuracy is statistically significantly above the majority class baseline (p < 0.05) using a label-shuffled control.

**Acceptance Scenarios**:

1. **Given** the DEAP dataset is available locally, **When** the preprocessing script runs on a single subject, **Then** the output is a feature matrix with dimensions matching the number of windows × (3 muscles × 4 features) and a corresponding label vector.
2. **Given** a trained SVM model, **When** evaluated on a held-out subject fold, **Then** the accuracy is statistically significantly above the majority class baseline (p < 0.05) using a label-shuffled control.
3. **Given** the full dataset, **When** the nested 5-fold cross-validation runs, **Then** the process completes within the 6-hour GitHub Actions time limit and memory usage remains < 7 GB.

### User Story 2 - Muscle-Specific Feature Importance Analysis (Priority: P2)

The system must quantify the contribution of each muscle group (corrugator, zygomaticus, orbicularis) to the classification performance using permutation importance and hierarchical feature addition, reporting the incremental pseudo-variance explained (Nagelkerke’s R² change).

**Why this priority**: This addresses the specific research question regarding "how much variance... can be explained by specific muscle groups." It moves beyond "does it work" to "which muscles drive the signal," providing the mechanistic insight required for the neuroscience contribution.

**Independent Test**: Can be tested by running the importance analysis module on the trained Random Forest model and verifying that the output includes a ranked list of muscle groups with associated importance scores and that the hierarchical Nagelkerke’s R² change is calculated for each addition.

**Acceptance Scenarios**:

1. **Given** the trained Random Forest model, **When** permutation importance is calculated, **Then** the output lists the top 10 features with their scores, grouped by muscle origin.
2. **Given** a hierarchical model sequence (Corrugator only → +Zygomaticus → +Orbicularis), **When** the pseudo-variance explained is computed, **Then** the report shows the Nagelkerke’s R² change for each step with a 95% confidence interval (calculated via bootstrap, 1000 iterations).
3. **Given** the SHAP values, **When** visualized (or summarized), **Then** the plot clearly distinguishes the contribution of positive-valence features (e.g., zygomaticus) from negative-valence features (e.g., corrugator).

### User Story 3 - Statistical Validation and Sensitivity Reporting (Priority: P3)

The system must generate a final report comparing observed accuracy to the label-shuffled baseline with effect sizes (Cohen’s d), and include a sensitivity analysis for the valence binarization threshold (±0.05, ±0.10) to ensure robustness.

**Why this priority**: This ensures methodological soundness. Without statistical validation, results are anecdotal. Without sensitivity analysis, the binary threshold choice is arbitrary and potentially biases the findings. This is required for the "Methodologically sound" criteria.

**Independent Test**: Can be tested by executing the reporting script and verifying the presence of a p-value, Cohen’s d, and a table showing accuracy variation across three different valence cutoffs.

**Acceptance Scenarios**:

1. **Given** the cross-validation results, **When** the statistical test runs, **Then** the report outputs a permutation test result (p < 0.05, based on 1000 shuffles) and Cohen’s d is calculated and reported.
2. **Given** the default valence cutoff of 5.0, **When** the sensitivity sweep runs with cutoffs [4.9, 5.0, 5.1], **Then** the report shows that accuracy varies by less than 3% across these thresholds.
3. **Given** the final analysis, **When** the report is generated, **Then** it explicitly states that findings are associational and not causal due to the observational nature of the DEAP dataset.

### Edge Cases

- What happens if a specific subject has missing EMG channels (e.g., bad electrode contact)? The system must skip that subject's data for that channel or impute using a median filter, but must log the exclusion in the final report.
- How does the system handle subjects with extremely skewed valence scores (e.g., all scores > 5 or all < 5)? The system must detect this class imbalance and exclude the subject from training to prevent model bias, logging the exclusion.
- What happens if the GitHub Actions runner runs out of disk space during intermediate feature storage? The system must process subjects sequentially and delete intermediate feature matrices immediately after processing each subject to ensure disk usage stays within acceptable operational limits.

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and extract the DEAP dataset from the official source ( certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)')))]) and validate file integrity via checksums. (See US-1)
- **FR-002**: System MUST apply a 10–500 Hz band-pass Butterworth filter and a 50 Hz notch filter to raw EMG signals before segmentation. (See US-1)
- **FR-003**: System MUST segment continuous signals into 1-second non-overlapping windows and perform baseline correction using the pre-stimulus interval. (See US-1)
- **FR-004**: System MUST extract four time-domain features (RMS, ZCR, WAMP, MAV) for each of the three muscle channels per window. (See US-1)
- **FR-005**: System MUST train a Support Vector Machine (linear kernel) and a Random Forest (100 trees) using nested 5-fold cross-validation with subject-level splitting. The Random Forest model MUST be used for all feature importance and variance explained analyses. (See US-1)
- **FR-006**: System MUST calculate permutation importance and SHAP values to rank feature contributions by muscle group. (See US-2)
- **FR-007**: System MUST perform hierarchical model fitting to estimate incremental pseudo-variance explained (Nagelkerke’s R² change) when adding muscle groups sequentially. (See US-2)
- **FR-008**: System MUST conduct a permutation test (1000 shuffles) comparing observed accuracy against a label-shuffled baseline (α = 0.05) and calculate Cohen’s d. (See US-3)
- **FR-009**: System MUST execute a sensitivity analysis sweeping the valence binarization threshold over {4.9, 5.0, 5.1} and report accuracy variation. (See US-3)
- **FR-010**: System MUST process data sequentially (subject-by-subject) and clear intermediate memory to ensure peak RAM usage remains < 7 GB. (See US-1)

### Key Entities

- **EMGWindow**: A data structure representing a 1-second segment of EMG data, containing attributes for time, subject ID, muscle channel, and feature vector.
- **ValenceLabel**: A binary label (0/1) derived from the subject's self-reported valence score, mapped based on the threshold (≥ 5 → 1, < 5 → 0).
- **FeatureMatrix**: A 2D array where rows represent windows and columns represent features (3 muscles × 4 features), used for model training.
- **ImportanceScore**: A metric quantifying the contribution of a specific feature or muscle group to the model's predictive performance.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Classification accuracy is measured against the majority class baseline and the label-shuffled distribution to confirm statistical significance (p < 0.05). (See US-1)
- **SC-002**: The proportion of pseudo-variance explained (Nagelkerke’s R²) by each muscle group is measured against the baseline model (intercept only) and the full model to quantify incremental contribution. (See US-2)
- **SC-003**: Model robustness is measured against variations in the valence binarization threshold (±0.05, ±0.10) to ensure results are not an artifact of a single arbitrary cutoff. (See US-3)
- **SC-004**: Computational feasibility is measured against the GitHub Actions free-tier constraints (≤ 6 hours runtime, < 7 GB RAM) to ensure the analysis is reproducible on standard CI. (See US-1)
- **SC-005**: Effect size (Cohen’s d) is measured against the null distribution of shuffled labels to quantify the magnitude of the improvement over chance. (See US-3)

## Assumptions

- The DEAP dataset contains valid, synchronized EMG recordings for the corrugator, zygomaticus, and orbicularis muscles for all participants., and the self-reported valence scores are complete.
- The relationship between facial EMG activity and emotional valence is associational; no causal claims are made as the dataset lacks random assignment of emotional stimuli or experimental manipulation of muscle activity.
- The 10–500 Hz band-pass filter and 50 Hz notch filter are sufficient to remove noise and powerline interference for the specific DEAP dataset recordings.
- The linear kernel SVM and Random Forest (100 trees) are computationally tractable on the GitHub Actions free-tier CPU-only environment for the given dataset size.
- The binarization threshold of 5.0 for valence scores is a standard community default; the sensitivity analysis will verify if small deviations significantly alter conclusions.
- The sample size provides sufficient statistical power for the cross-validation approach., though this is acknowledged as a limitation for generalization to broader populations.
- No GPU acceleration is required or available; all signal processing and machine learning tasks must rely on CPU-optimized libraries (scikit-learn, scipy, numpy).
- The DEAP dataset's self-reported valence scores are treated as the ground truth, despite the inherent subjectivity and potential noise in self-reporting methods.