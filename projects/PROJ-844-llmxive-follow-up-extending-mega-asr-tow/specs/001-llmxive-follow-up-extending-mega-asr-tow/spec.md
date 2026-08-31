# Feature Specification: llmXive Follow-up: Extending "Mega-ASR" for Semantic Collapse Thresholds

**Feature Branch**: `001-semantic-collapse-threshold`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "Do non-linear interactions between specific acoustic distortion types create a universal 'semantic collapse threshold' that cannot be predicted by the sum of individual distortion effects?"

## User Stories & Testing

### User Story 1 - Generate Compound Distortion Stress Curves (US-1) (Priority: P1)

**User Journey**: A researcher needs to systematically apply a diverse set of compound acoustic distortions (combinations of reverberation and noise) to a stratified subset of the **Voices-in-the-Wild-2M** dataset to generate stress curves for small ASR models.

**Why this priority**: This is the foundational data generation step. Without the stress curves (mapping distortion intensity to semantic integrity), no analysis of non-linear interactions or collapse thresholds is possible. It delivers the raw dataset required for the entire study.

**Independent Test**: Can be fully tested by running the stress‑testing pipeline on a representative sample of audio clips (e.g., several clips) and verifying that for each clip, the system generates a comprehensive set of distinct distortion scenarios (based on the defined Cartesian product grid of SNR levels × RT60 levels), resulting in a CSV/JSON file containing the acoustic parameters, the ASR output, and the semantic similarity score for each scenario. The test validates the *process* of generating 54 scenarios per clip, regardless of the total subset size.

**Acceptance Scenarios**:

1. **Given** a clean audio clip from the stratified subset, **When** the system applies the 54 compound distortion vectors with incrementally increasing intensity parameters, **Then** the system outputs a record for each distortion level containing the specific parameters (SNR, RT60), the ASR hypothesis, and the calculated Semantic Similarity Score (SSS).
2. **Given** the generated stress curve data, **When** a user queries for a specific model (e.g., Whisper‑tiny) and a specific distortion type (e.g., "Far‑field + Echo"), **Then** the system returns the ordered sequence of SSS scores corresponding to increasing distortion intensity.

### User Story 2 - Identify Semantic Collapse Points (US-2) (Priority: P2)

**User Journey**: A researcher needs to automatically identify the precise "collapse intensity" for each model/scenario combination, defined primarily by the inflection point of the degradation curve (maximum derivative) and secondarily by a concurrent SSS drop below a baseline‑normalized threshold and WER spike.

**Why this priority**: This transforms raw stress curves into a scalar target variable required for the regression analysis. It isolates the specific failure event from the continuous degradation curve and ensures the target is not circularly dependent on a single metric.

**Independent Test**: Can be fully tested by providing a pre‑calculated stress curve where the SSS decreases monotonically from a high to a low value between two known intensity steps, and verifying that the system correctly identifies the interpolation point (or the specific step) where the normalized SSS first falls below the baseline‑normalized threshold **and** the WER exceeds the specified multiple of the baseline, recording this as the collapse intensity. The test must also verify that if SSS and WER disagree on the step, the system uses the deterministic interpolation rule defined in FR‑020.

**Acceptance Scenarios**:

1. **Given** a stress curve where the SSS decreases monotonically from 0.9 to 0.1, **When** the system processes the data, **Then** it identifies and records the specific distortion intensity vector where the normalized SSS first falls below the baseline‑normalized threshold **and** the WER significantly exceeds the model's baseline WER. (Baseline calculated on the clean subset of the Voices‑in‑the‑Wild‑2M dataset).
2. **Given** a stress curve where the SSS never drops below the threshold across the tested intensity range, **When** the system processes the data, **Then** it records the collapse intensity as "None" or "Max Tested" to indicate the model remained robust within the tested bounds.

### User Story 3 - Predict Collapse via Critical Interaction Vector (US-3) (Priority: P3)

**User Journey**: A researcher needs to train a lightweight regression model to predict the identified collapse intensities based solely on the acoustic parameter vectors (including engineered interaction terms), and then validate if a universal "critical interaction vector" exists across different ASR models.

**Why this priority**: This is the core scientific hypothesis test. It determines if the "semantic collapse threshold" is a predictable, universal phenomenon or an idiosyncratic failure mode, directly addressing the research question.

**Independent Test**: Can be fully tested by splitting the dataset into training and held‑out test sets (stratified by speaker ID and distortion type), training the regression model on the training set, and verifying that the model achieves a predefined correlation coefficient (R² ≥ 0.6) between predicted and actual collapse intensities on the test set. The test must also verify that a permutation baseline (FR‑027) yields an R² drop of at least 0.20, confirming the model learns genuine structure. Finally, a model‑agnostic SHAP analysis must be performed to confirm the form of interaction.

**Acceptance Scenarios**:

1. **Given** the dataset of acoustic parameter vectors (including interaction terms) and their corresponding collapse intensities, **When** the regression model is trained and evaluated on a held‑out test set, **Then** the system outputs the model performance metrics (R² ≥ 0.6, MAE) and the coefficients representing the "critical interaction vector."
2. **Given** the trained predictor, **When** the system compares the critical interaction vectors across the set of small ASR models, **Then** it reports the degree of similarity (cosine similarity ≥ 0.80) between the vectors to assess generalizability.

### Edge Cases

- What happens when the semantic similarity score oscillates around the 0.5 baseline‑normalized threshold due to noise in the embedding model? (System must implement a smoothing/hysteresis mechanism to define a stable collapse intensity).
- How does the system handle audio clips where the ASR model fails completely (outputs empty string) before the threshold is theoretically reached? (System maps this to a collapse intensity at the lowest tested intensity).
- What if the Voices‑in‑the‑Wild‑2M subset lacks specific distortion combinations required for the 54 scenarios? (System logs a warning and proceeds with the available subset, noting the missing scenarios in the final report).

## Requirements

### Functional Requirements

- **FR-001**: System MUST download and stratify a subset of **≥ 50,000** audio clips from the **Voices-in-the-Wild-2M** dataset, ensuring coverage of a comprehensive set of compound distortion scenarios via a metadata‑based sampling strategy using a pre‑computed index to stratify by speaker ID and recording environment (as proxies for acoustic conditions), specifically ensuring inclusion of high RT60 and low SNR conditions. The sample size of ≥ 50,000 provides ≥ 80 % power to detect an effect size f² ≥ 0.02 at α = 0.05 for the regression analysis in US‑3 (power analysis performed with G*Power, required N [deferred]) (See US‑1).
- **FR-002**: System MUST apply a series of distinct compound acoustic distortion vectors (varying reverberation time and SNR) to each clean audio clip using physical acoustic models (e.g., pyroomacoustics), incrementally increasing intensity to generate stress curves. The generation phase MUST be executed via a distributed GPU‑enabled computing environment (e.g., Kubernetes with GPU nodes) to handle the workload of **≥ 50,000 clips × 54 scenarios × 5 models** within a 48‑hour wall‑time budget (See US‑1).
- **FR-003**: System MUST compute the Semantic Similarity Score (SSS) between the clean reference transcript and the distorted ASR hypothesis using the **all‑MiniLM‑L6‑v2** model (source: Q801455, https://www.wikidata.org/wiki/Q801455). (See US‑1)
- **FR-004**: System MUST identify the "semantic collapse intensity" for each model/scenario combination by executing the deterministic algorithm defined in **FR‑021**. (See US‑2)
- **FR-005**: System MUST train a regression model to predict the scalar **collapse intensity** (as defined in FR‑021) from the acoustic parameter vector (including engineered interaction terms SNR × RT60, SNR², RT60²). The system MUST use a stratified split by speaker ID and distortion type for training and validation. The system MUST perform a permutation baseline test (FR‑027) to demonstrate that performance degrades ≥ 0.20 R² when predictors are randomly permuted, ensuring the model learns genuine structure rather than the deterministic rule.
- **FR-006**: System MUST perform a sensitivity analysis by sweeping the inflection‑point detection parameters (SSS threshold ∈ {low, medium, high} × baseline, WER multiplier ∈ {a lower value, 2, 2.5}) and analyzing the variance in the identified "critical interaction vector" across different curve morphologies (linear vs. sigmoid). (See US‑3)
- **FR-007**: System MUST explicitly frame all predictive findings as ASSOCIATIONAL, avoiding causal claims regarding the distortions unless randomization is explicitly modeled. (See US‑3)
- **FR-008**: System MUST perform multiple‑comparison correction (Benjamini‑Hochberg FDR ≤ 0.05) when evaluating the statistical significance of the interaction effects across the 54 scenarios. (See US‑3)
- **FR-010**: System MUST normalize the SSS collapse threshold relative to each model's clean‑audio baseline SSS (threshold = 0.5 × baseline SSS) to isolate universal acoustic interactions from model‑specific embedding behaviours. (See US‑3)
- **FR-011**: System MUST validate the SSS metric against a held‑out subset of **≥ 1,000** human‑annotated transcripts (sourced from the Voices‑in‑the‑Wild‑2M dataset, stratified by speaker and environment) to ensure correlation with human judgment of semantic integrity. The human annotations MUST be obtained via a crowdsourcing protocol with **≥ 3** raters per clip, requiring **≥ 2⁄3** agreement on a binary intelligibility score (pass/fail). The validation MUST achieve **AUC‑ROC ≥ 0.85** as the pass criterion. (See US‑1)
- **FR-012**: System MUST analyze the shape of each degradation curve (e.g., sigmoid vs. linear) and calculate the maximum derivative (inflection point) for every stress curve to normalize the rate of degradation across models. (See US‑2)
- **FR-013**: System MUST explicitly validate the non‑linear nature of interactions by comparing the interaction term coefficient against the sum of individual coefficients in a linear additive model of SSS vs. SNR/RT60, confirming synergistic failure modes. The comparison MUST use a statistically significant (p < 0.05, FDR‑corrected) improvement in variance explained by the full model over the additive model. (See US‑3)
- **FR-016**: System MUST halt the workflow and require manual intervention if FR‑011 (human validation) fails to meet the threshold (AUC‑ROC ≥ 0.85) **AND** the fallback mechanism in FR‑022 also fails to achieve the threshold for the phoneme metric (Pearson r ≥ 0.6). This check is performed as a pre‑study gate before US‑1 execution. (See US‑1)
- **FR-017**: System MUST log a warning and proceed with the available subset, noting the missing scenarios in the final report, if the Voices‑in‑the‑Wild‑2M subset lacks specific distortion combinations required for the 54 scenarios. (See US‑1)
- **FR-018**: System MUST validate the realism of applied synthetic distortions against a subset of **≥ 50** real‑world noisy audio clips (sourced from the DNS‑Challenge real‑world noise subset). Validation MUST use a Log‑Mel Spectral Distance (LMSD) metric (window = 25 ms, hop = 10 ms, 128 bins) with a pass criterion of **≤ 0.15**. The matching protocol MUST minimize the distance between the synthetic clip and a real‑world clip with similar SNR/RT60 estimates (within ± 1 dB / ± 0.1 s). (See US‑1)
- **FR-020**: System MUST implement a deterministic interpolation rule for the 'concurrent' check: if normalized SSS drops below the baseline‑normalized threshold at step N and WER spikes at the subsequent step, the collapse intensity is defined as the linearly interpolated intensity between steps N and N+1. The rule must be evaluated across the sensitivity‑analysis parameter grid defined in FR‑006. (See US‑2)
- **FR-021**: System MUST implement the following deterministic algorithm to calculate 'collapse intensity':
    1. Calculate the first derivative of the SSS curve.
    2. Identify the inflection point (maximum negative derivative).
    3. Determine the "threshold crossing step": the first step where **normalized** SSS < 0.5 × baseline SSS **AND** WER > 2 × baseline WER (baseline WER calculated on the clean subset of the Voices‑in‑the‑Wild‑2M dataset).
    4. If the threshold crossing step exists: Record the intensity at that step (or linearly interpolated intensity if steps differ per FR‑020) as 'collapse intensity'.
    5. If no threshold crossing step exists but an inflection point exists: Record the inflection point intensity as 'collapse intensity' (indicating a slow degradation).
    6. If neither exists: Record 'None'. (See US‑2)
- **FR-022**: System MUST implement a fallback mechanism: if the embedding model fails to correlate with human judgment for high‑reverb audio (RT60 > 0.5 s) with AUC‑ROC < 0.85, the system MUST switch to a phoneme‑level edit distance metric (using Montreal Forced Aligner with standard English dictionaries) as the primary semantic integrity measure for that subset. The phoneme‑level edit distance MUST be calculated against the original clean transcript from the Voices‑in‑the‑Wild‑2M dataset. The high‑reverb subset MUST be **≥ 500** clips, stratified by speaker ID. (See US‑1)
- **FR-023**: System MUST define the specific values for all parameters before execution: sample size = 50,000 clips; effect size f² = 0.02; power = 0.80; α = 0.05; correlation threshold R² ≥ 0.6; FDR threshold ≤ 0.05; SSS baseline‑normalized threshold = 0.5 × baseline; WER multiplier = 2× baseline. (See US‑1)
- **FR-024**: System MUST generate the distortion scenarios using a Cartesian product of **9** SNR levels and **6** RT60 levels to produce a diverse set of distinct scenarios. (See US‑1)
- **FR-025**: System MUST utilize a hierarchical regression model or functional data analysis approach to account for model‑specific idiosyncrasies when predicting the "critical interaction vector" across different ASR architectures, ensuring the statistical method matches the research goal. (See US‑3)
- **FR-026**: System MUST log the actual computation steps, data sources, and intermediate values for every metric (SSS, WER, R²) to ensure auditability and prevent the use of simulated or fabricated scores. (See US‑1)
- **FR-027**: System MUST perform a permutation baseline test: randomly permute acoustic predictor vectors across samples, retrain the regression model, and verify that the resulting R² drops by **≥ 0.20** compared to the non‑permuted model, demonstrating that the learned relationship is not a trivial consequence of the deterministic collapse definition. (See US‑3)

### Key Entities

- **AudioClip**: Represents a single audio file from the dataset, containing metadata (ID, source, speaker_id, environment_id) and the raw waveform.
- **DistortionVector**: Represents a specific combination of acoustic parameters (e.g., SNR=10 dB, RT60=0.5 s, DistortionType=Reverb+Noise).
- **StressCurve**: A sequence of records linking a specific AudioClip and DistortionVector to a resulting SSS and ASR hypothesis.
- **CollapseIntensity**: A derived entity representing the specific DistortionVector intensity where the normalized SSS < 0.5 × baseline and WER > 2× baseline for a given model.
- **CriticalInteractionVector**: The learned coefficients from the regression model representing the predictive signature of semantic collapse.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The predictive accuracy (R² score) of the regression model is measured against the held‑out test set (stratified 80/20 by speaker ID and distortion type) of collapse intensities to determine if a universal interaction signature exists. Success is defined as **R² ≥ 0.6**. (See US‑3)
- **SC-002**: The stability of the "critical interaction vector" is measured against the sensitivity analysis results; stability is quantified by a **coefficient of variation ≤ 0.10** across all sensitivity‑analysis parameter settings. (See US‑3)
- **SC-003**: The statistical significance of the non‑linear interaction terms is measured against the corrected p‑values (post‑Benjamini‑Hochberg adjustment, threshold < 0.05) to validate the synergistic failure hypothesis. (See US‑3)
- **SC-004**: The computational feasibility is measured against the successful completion of the distributed stress‑test pipeline on the specified GPU‑enabled cluster environment within **48 hours**. (See US‑1, US‑3)
- **SC-005**: The similarity of critical interaction vectors across different ASR models is measured by **cosine similarity ≥ 0.80**; values below this indicate model‑specific divergence. (See US‑3)
- **SC-006**: The external validity of the SSS metric is measured against the human‑annotated subset (FR‑011) with an **AUC‑ROC ≥ 0.85**. (See US‑1)
- **SC-009**: For US‑2, the identification of collapse points must achieve **precision ≥ 0.90** and **recall ≥ 0.90** when compared against manually annotated ground‑truth collapse intensities on a validation subset of 500 stress curves. (See US‑2)

## Assumptions

- The **Voices-in-the-Wild-2M** dataset contains sufficient clean audio segments to support the generation of a **≥ 50,000**‑clip subset with valid ground‑truth transcripts for stress testing.
- The `all‑MiniLM‑L6‑v2` model is a valid, CPU‑tractable proxy for "semantic integrity" and its embeddings correlate sufficiently with human judgment of ASR failure for the purpose of defining the baseline‑normalized threshold (validated via FR‑011 and FR‑022).
- The compound distortion scenarios (combinations of reverberation and noise) are physically realizable and cover the relevant non‑linear interaction space for the research question.
- The selected small ASR models (e.g., Whisper‑tiny, Distil‑Whisper) can perform inference on GPU‑enabled nodes within the memory limits of the distributed environment without requiring quantization.
- The relationship between acoustic distortion parameters and semantic collapse is complex and non‑linear, requiring hierarchical modeling or functional data analysis to isolate universal acoustic interactions from model‑specific variance in the target variable.
- The "semantic collapse" phenomenon is consistent enough across different small ASR architectures to justify the cross‑model generalization check.
- The 54 distortion scenarios are generated using the Cartesian product defined in FR‑024 (9 SNR levels × 6 RT60 levels).
- The Voices‑in‑the‑Wild‑2M dataset provides the necessary metadata fields (speaker_id, environment_id, clean_transcript) to support the stratified sampling strategy described in FR‑001.
- The DNS‑Challenge dataset contains real‑world noisy audio clips that can be matched to synthetic parameters within the specified tolerance (±1 dB / ±0.1 s) for the realism validation in FR‑018.
- The crowdsourcing protocol for human annotations (FR‑011) will yield a sufficient number of high‑quality binary intelligibility scores to validate the SSS metric.
