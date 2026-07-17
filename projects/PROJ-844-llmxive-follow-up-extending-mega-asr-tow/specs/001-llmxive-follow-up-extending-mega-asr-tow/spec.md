# Feature Specification: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Feature Branch**: `001-semantic-collapse-threshold`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "Do non-linear interactions between specific acoustic distortion types create a universal 'semantic collapse threshold' that cannot be predicted by the sum of individual distortion effects?"

## User Scenarios & Testing

### User Story 1 - Generate Compound Distortion Stress Curves (Priority: P1)

**User Journey**: A researcher needs to systematically apply a diverse set of compound acoustic distortions (combinations of reverberation and noise) to a subset of the "Voices-in-the-Wild-2M" dataset to generate stress curves for small ASR models.

**Why this priority**: This is the foundational data generation step. Without the stress curves (mapping distortion intensity to semantic integrity), no analysis of non-linear interactions or collapse thresholds is possible. It delivers the raw dataset required for the entire study.

**Independent Test**: Can be fully tested by running the stress-testing pipeline on a sample of 100 audio clips and verifying that for each clip, 54 distinct distortion scenarios are applied, resulting in a CSV/JSON file containing the acoustic parameters, the ASR output, and the semantic similarity score for each scenario.

**Acceptance Scenarios**:

1. **Given** a clean audio clip from the stratified subset, **When** the system applies the 54 compound distortion vectors with incrementally increasing intensity parameters, **Then** the system outputs a record for each distortion level containing the specific parameters (SNR, RT60), the ASR hypothesis, and the calculated Semantic Similarity Score (SSS).
2. **Given** the generated stress curve data, **When** a user queries for a specific model (e.g., Whisper-tiny) and a specific distortion type (e.g., "Far-field + Echo"), **Then** the system returns the ordered sequence of SSS scores corresponding to increasing distortion intensity.

### User Story 2 - Identify Semantic Collapse Points (Priority: P2)

**User Journey**: A researcher needs to automatically identify the precise "collapse intensity" for each model/scenario combination, defined as the specific stress level where the Semantic Similarity Score (SSS) drops below a critical threshold (normalized to 0.5 relative to baseline) AND is confirmed by a concurrent Word Error Rate (WER) spike.

**Why this priority**: This transforms raw stress curves into a binary or scalar target variable (the collapse intensity) required for the regression analysis. It isolates the specific failure event from the continuous degradation curve and ensures the target is not circularly dependent on a single metric.

**Independent Test**: Can be fully tested by providing a pre-calculated stress curve where the SSS drops from 0.8 to 0.4 between two known intensity steps, and verifying that the system correctly identifies the interpolation point (or the specific step) where the normalized 0.5 threshold is crossed AND the WER exceeds 2× the baseline, recording this as the collapse intensity.

**Acceptance Scenarios**:

1. **Given** a stress curve where the SSS decreases monotonically from 0.9 to 0.1, **When** the system processes the data, **Then** it identifies and records the specific distortion intensity vector where the normalized SSS first falls below 0.5 AND the WER exceeds the validated spike threshold.
2. **Given** a stress curve where the SSS never drops below the threshold across the tested intensity range, **When** the system processes the data, **Then** it records the collapse intensity as "None" or "Max Tested" to indicate the model remained robust within the tested bounds.

### User Story 3 - Predict Collapse via Critical Interaction Vector (Priority: P3)

**User Journey**: A researcher needs to train a lightweight regression model to predict the identified collapse intensities based solely on the acoustic parameter vectors (including engineered interaction terms), and then validate if a universal "critical interaction vector" exists across different ASR models.

**Why this priority**: This is the core scientific hypothesis test. It determines if the "semantic collapse threshold" is a predictable, universal phenomenon or an idiosyncratic failure mode, directly addressing the research question.

**Independent Test**: Can be fully tested by splitting the dataset into training and held-out test sets, training the regression model on the training set, and verifying that the model achieves a predefined correlation coefficient (e.g., R² > 0.6) between predicted and actual collapse intensities on the test set.

**Acceptance Scenarios**:

1. **Given** the dataset of acoustic parameter vectors (including interaction terms) and their corresponding collapse intensities, **When** the regression model is trained and evaluated on a held-out test set, **Then** the system outputs the model performance metrics (R², MAE) and the coefficients representing the "critical interaction vector."
2. **Given** the trained predictor, **When** the system compares the critical interaction vectors across the 5-10 different small ASR models, **Then** it reports the degree of similarity (e.g., cosine similarity) between the vectors to assess generalizability.

### Edge Cases

- What happens when the semantic similarity score oscillates around the 0.5 threshold due to noise in the embedding model? (System must implement a smoothing or hysteresis mechanism to define a stable collapse intensity).
- How does the system handle audio clips where the ASR model fails completely (outputs empty string) before the 0.5 SSS threshold is theoretically reached? (System must map this to a collapse intensity at the lowest tested intensity).
- What if the "Voices-in-the-Wild-2M" subset lacks specific distortion combinations required for the 54 scenarios? (System must log a warning and proceed with the available subset, noting the missing scenarios in the final report).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and stratify a subset of [deferred] audio clips from the "Voices-in-the-Wild-2M" dataset, ensuring coverage of the 54 compound distortion scenarios via stratification by speaker ID and SNR bucket. (See US-1)
- **FR-002**: System MUST apply 54 distinct compound acoustic distortion vectors (varying reverberation time and SNR) to each clean audio clip, incrementally increasing intensity to generate stress curves. (See US-1)
- **FR-003**: System MUST compute the Semantic Similarity Score (SSS) between the clean reference transcript and the distorted ASR hypothesis using the `all-MiniLM-L6-v2` sentence embedding model. (See US-1)
- **FR-004**: System MUST identify the "semantic collapse intensity" for each model/scenario combination as the specific distortion intensity where the SSS first drops below 0.5 (normalized to baseline) AND is corroborated by a concurrent WER spike. (See US-2)
- **FR-005**: System MUST train a CPU-tractable regression model (e.g., scikit-learn Linear Regression, Polynomial Regression with degree ≤ 3, or Decision Tree with max_depth ≤ 5) to predict the collapse intensity based on the acoustic parameter vector, explicitly including engineered interaction terms (e.g., SNR × RT60, SNR², RT60²). (See US-3)
- **FR-006**: System MUST perform a sensitivity analysis by sweeping the collapse threshold from 0.40 to 0.60 in increments of 0.05 and report the variance in the identified "critical interaction vector." (See US-3)
- **FR-007**: System MUST explicitly frame all predictive findings as ASSOCIATIONAL, avoiding causal claims regarding the distortions unless randomization is explicitly modeled. (See US-3)
- **FR-008**: System MUST implement multiple-comparison correction (e.g., Bonferroni or False Discovery Rate) when evaluating the statistical significance of the interaction effects across the 54 scenarios. (See US-3)
- **FR-009**: System MUST validate the identified collapse intensity by confirming a concurrent spike in Word Error Rate (WER) exceeding 2× the model's baseline WER to ensure the target is not circularly dependent on the SSS metric. (See US-2)
- **FR-010**: System MUST normalize the SSS collapse threshold (0.5) relative to each model's clean-audio baseline SSS to isolate universal acoustic interactions from model-specific embedding behaviors. (See US-3)
- **FR-011**: System MUST validate the SSS metric against a held-out subset of human-annotated transcripts to ensure correlation with human judgment of semantic integrity before defining the collapse threshold. (See US-1)

### Key Entities

- **AudioClip**: Represents a single audio file from the dataset, containing metadata (ID, source) and the raw waveform.
- **DistortionVector**: Represents a specific combination of acoustic parameters (e.g., SNR=10dB, RT60=0.5s, DistortionType=Reverb+Noise).
- **StressCurve**: A sequence of records linking a specific AudioClip and DistortionVector to a resulting SSS and ASR hypothesis.
- **CollapseIntensity**: A derived entity representing the specific DistortionVector intensity where SSS < 0.5 (normalized) for a given model.
- **CriticalInteractionVector**: The learned coefficients from the regression model representing the predictive signature of semantic collapse.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive accuracy (R² score) of the regression model is measured against the held-out test set of collapse intensities to determine if a universal interaction signature exists. (See US-3)
- **SC-002**: The stability of the "critical interaction vector" is measured against the results of the sensitivity analysis (threshold sweep) to ensure the findings are not artifacts of the 0.5 cutoff choice. (See US-3)
- **SC-003**: The statistical significance of the non-linear interaction terms is measured against the corrected p-values (post-multiple-comparison adjustment) to validate the synergistic failure hypothesis. (See US-3)
- **SC-004**: The computational feasibility is measured against the 6-hour runtime limit and 7GB RAM constraint on the GitHub Actions ubuntu-latest runner, tracking peak RSS memory usage and total wall-clock time, to ensure the analysis is reproducible without GPU. (See US-1, US-3)

## Assumptions

- The "Voices-in-the-Wild-2M" dataset contains sufficient clean audio segments to support the generation of a [deferred] number of clips with valid ground truth transcripts for the stress testing.
- The `all-MiniLM-L6-v2` model is a valid, CPU-tractable proxy for "semantic integrity" and its embeddings correlate sufficiently with human judgment of ASR failure for the purpose of defining the 0.5 threshold (validated via FR-011).
- The 54 compound distortion scenarios (combinations of reverberation and noise) are physically realizable and cover the relevant non-linear interaction space for the research question.
- The 5-10 selected small ASR models (e.g., Whisper-tiny, Distil-Whisper) can perform inference on CPU within the 7GB RAM limit without requiring quantization or GPU acceleration.
- The relationship between acoustic distortion parameters and semantic collapse is primarily linear or low-order polynomial, allowing a simple regression model with interaction terms to capture the "critical interaction vector" effectively.
- The "semantic collapse" phenomenon is consistent across different small ASR architectures, justifying the cross-model generalization check.