# Feature Specification: llmXive follow-up: extending "EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents"

**Feature Branch**: `001-gene-regulation`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'EVA-Bench: A New End-to-end Framework for Evaluating Voice Agents' - Research question: How does the injection of asynchronous network latency (jitter and variable inter-turn delays) into voice agent simulations degrade specific EVA-Bench 'Turn-Taking' and 'Conversation Progression' metrics compared to static acoustic perturbations, and at what latency threshold does a non-linear failure mode emerge?"

## User Scenarios & Testing

### User Story 1 - Latency Injection Pipeline (Priority: P1)

**Description**: As a researcher, I need a reliable mechanism to inject variable network latency (jitter and inter-turn delays ranging from ms to high magnitudes) into the EVA-Bench scenario audio streams so that I can simulate real-world network conditions without modifying the original agent models.

**Why this priority**: This is the foundational data generation step. Without the ability to systematically perturb the audio inputs with controlled latency, the subsequent evaluation and statistical analysis cannot occur. It is the prerequisite for all other stories.

**Independent Test**: The system is tested by running the `LatencyInjector` on a single EVA-Bench scenario file with a fixed 500ms delay and verifying that the output audio file has a duration strictly greater than the input duration, while preserving the original audio content elsewhere.

**Acceptance Scenarios**:

1. **Given** a valid EVA-Bench scenario audio file, **When** the injector is configured with a 800ms inter-turn delay, **Then** the output audio file must have a silent gap of appropriate duration inserted at the designated turn boundary.
2. **Given** a set of scenario files, **When** the injector is run with a jitter parameter of ±50ms, **Then** the inserted gaps must vary randomly within the specified range across multiple runs, while the mean gap remains at the target value.
3. **Given** an audio file exceeding 7GB in size (simulated via chunking), **When** the injector processes it, **Then** the The process must complete without exceeding a predetermined RAM threshold by processing in chunks..

---

### User Story 2 - EVA-Bench Re-evaluation (Priority: P2)

**Description**: As a researcher, I need to re-run the original EVA-Bench scoring logic on the latency-perturbed audio streams to generate new EVA-A (Accuracy) and EVA-X (Experience) scores, specifically isolating the "Turn-Taking" and "Conversation Progression" sub-metrics.

**Why this priority**: This step generates the dependent variable data. It validates that the injection pipeline successfully interacts with the evaluation framework and produces comparable metrics to the baseline.

**Independent Test**: The system is tested by comparing the original baseline scores (0ms latency) against the scores generated from the same scenarios with 0ms latency injected; the delta must be zero within a floating-point tolerance., confirming the evaluator logic is unchanged and the pipeline is stable.

**Acceptance Scenarios**:

1. **Given** a set of latency-perturbed audio files, **When** the EVA-Bench evaluation pipeline is executed, **Then** the system must output a CSV containing the new EVA-X "Turn-Taking" and "Conversation Progression" scores for each scenario.
2. **Given** a scenario where the injected latency causes a turn-taking failure, **When** the evaluation runs, **Then** the "Turn-Taking" score must reflect a degradation compared to the baseline (delta < 0).
3. **Given** the full 213 scenarios, **When** processed in parallel across 2 CPU cores, **Then** the total execution time must remain within 6 hours to ensure adherence to the CI limit.

---

### User Story 3 - Threshold Detection & Statistical Analysis (Priority: P3)

**Description**: As a researcher, I need the system to perform a Linear Mixed-Effects Model (LMM) and segmented regression analysis on the score deltas to identify the specific latency "knee point" (threshold) where non-linear degradation occurs and to verify the statistical significance of the findings.

**Why this priority**: This is the core research output. It transforms raw data into the scientific answer regarding the latency threshold and failure modes.

**Independent Test**: The system is tested by feeding it a synthetic dataset with a known linear drop until 800ms and a sharp drop thereafter; the analysis module must correctly identify the break point at 800ms with a p-value < 0.05 for the non-linearity.

**Acceptance Scenarios**:

1. **Given** the delta scores across latency levels (continuous variable), **When** the LMM is run, **Then** the system must output a p-value indicating whether the effect of latency on scores is statistically significant.
2. **Given** the score-vs-latency data, **When** the segmented regression model is fitted, **Then** the system must report the specific "knee point" latency value where the slope of degradation significantly increases.
3. **Given** multiple hypothesis tests (one for Turn-Taking, one for Progression), **When** the analysis completes, **Then** the system must apply a multiple-comparison correction (e.g., Bonferroni) and report adjusted p-values.

---

### User Story 4 - Static Acoustic Perturbation Arm (Priority: P4)

**Description**: As a researcher, I need to apply static acoustic perturbations (e.g., white noise, reverberation) to a subset of the EVA-Bench scenarios to establish a control condition, allowing for a comparison between latency-induced degradation and acoustic-induced degradation.

**Why this priority**: The research question explicitly asks for a comparison against "static acoustic perturbations". Without this arm, the study cannot distinguish whether degradation is unique to latency or a general artifact of signal perturbation.

**Independent Test**: The system is tested by applying a fixed noise floor to a scenario and verifying that the EVA-X "Conversation Progression" score changes, while the "Turn-Taking" score (if perceptual) remains stable or changes differently than with latency injection.

**Acceptance Scenarios**:

1. **Given** a valid EVA-Bench scenario audio file, **When** the `AcousticPerturber` is run with a signal-to-noise ratio of 15dB, **Then** the output audio must contain the added noise without altering the timing of turn boundaries.
2. **Given** the perturbed audio, **When** the EVA-Bench evaluation pipeline is executed, **Then** the system must output a CSV containing the EVA-X scores for the acoustic condition.
3. **Given** both latency and acoustic results, **When** the analysis runs, **Then** the system must report a comparative metric (e.g., interaction effect) indicating if latency causes distinct degradation patterns.

### Edge Cases

- **Audio Length Limit**: If the injected latency causes the audio stream to exceed the EVA-Bench maximum duration, the system MUST truncate the audio to 5 minutes, log a warning, and record the score as `null` for that scenario.
- **Floor Effect**: If the baseline EVA-Bench score is already 0, the system MUST skip the delta calculation for that specific metric and record the delta as 0, logging a "floor effect" warning.
- **Parsing Error**: If the network jitter simulation results in a gap that overlaps with a spoken segment due to parsing errors, the system MUST revert to the nearest safe turn boundary (±50ms), log the correction, and proceed.

## Requirements

### Functional Requirements

- **FR-001**: System MUST implement a `LatencyInjector` that inserts silent gaps of variable duration (200ms–2000ms) and jitter (±50ms) at turn boundaries in EVA-Bench audio files (See US-1).
- **FR-002**: System MUST execute the original EVA-Bench evaluation pipeline on the perturbed audio files to generate new EVA-A and EVA-X scores without modifying the original scoring logic (See US-2).
- **FR-003**: System MUST calculate the delta ($\Delta$) between baseline scores and perturbed scores for each of the **evaluated systems** across the 213 scenarios (See US-2).
- **FR-004**: System MUST perform a **Linear Mixed-Effects Model (LMM)** to test for significant differences in "Turn-Taking" and "Conversation Progression" scores across the continuous latency variable (See US-3).
- **FR-005**: System MUST fit a segmented regression model to the score-vs-latency data to identify the specific "knee point" where the slope of degradation significantly increases (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Holm-Bonferroni) when reporting p-values for the LMM results (See US-3).
- **FR-007**: System MUST process audio files in chunks to ensure peak RAM usage remains within acceptable system limits during the injection and evaluation phases (See US-1).
- **FR-008**: System MUST implement an `AcousticPerturber` that adds static noise or reverberation to audio files without altering turn boundaries (See US-4).
- **FR-009**: System MUST generate a comparative report between the latency-induced degradation and the acoustic-induced degradation (See US-4).
- **FR-010**: System MUST validate the EVA-X "Turn-Taking" metric definition; if the metric is computationally dependent on raw timing, the system MUST flag this tautology risk and adjust the analysis to isolate perceptual effects (See US-2).
- **FR-011**: If the EVA-Bench audio logs are missing, the system MUST generate synthetic audio representations of multiple systems using a TTS engine with known characteristics to proceed with the experiment (See Assumptions).

### Key Entities

- **Scenario**: Represents a single entry from the EVA-Bench 213-scenario suite, containing the original audio file path and metadata.
- **PerturbationProfile**: Defines the specific latency conditions (mean delay, jitter range) or acoustic conditions (SNR, reverberation time) applied to a set of scenarios.
- **EvaluationResult**: Contains the computed EVA-A and EVA-X scores (specifically Turn-Taking and Conversation Progression) for a specific Scenario under a specific PerturbationProfile.
- **ThresholdModel**: The output of the segmented regression, containing the identified knee point latency and the slopes of the degradation curves.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The latency injection mechanism MUST be validated by confirming that the output audio duration increases by the target delay value **within ±1 sample of the target delay** relative to the sampling rate, measured against the original file metadata (See US-1, FR-001).
- **SC-002**: The statistical analysis MUST **report the p-value and apply the alpha=0.05 threshold** for the effect of latency on EVA-X "Conversation Progression" scores, measured against the null hypothesis of no effect (See US-3, FR-004, FR-006).
- **SC-003**: The segmented regression model MUST **report the slope ratio and flag if it exceeds a predefined threshold**, measured against the fitted model parameters (See US-3, FR-005).
- **SC-004**: The entire analysis pipeline (injection + evaluation + statistics) for the full 213 scenarios MUST complete within 6 hours on a 2-CPU, 7GB RAM runner, measured against the CI job timeout limit (See US-1, FR-007).
- **SC-005**: The sensitivity analysis for the threshold detection MUST report the variation in the identified "knee point" when the decision cutoff is swept over a range of ±50ms, measured against the stability of the reported threshold (See US-3).
- **SC-006**: The comparative analysis MUST report the interaction effect between perturbation type (latency vs. acoustic) and metric degradation, measured against the comparative report output (See US-4, FR-009).

## Assumptions

- The EVA-Bench repository (or arXiv supplementary link) contains downloadable audio logs for the evaluated systems and the scenario definitions, and these are accessible via `wget` without authentication. **If this assumption is false, FR-011 (synthetic audio generation) MUST be triggered.**
- The original EVA-Bench evaluation code is compatible with the Python environment available on the GitHub Actions free-tier runner (Python 3.x, standard libraries, `scipy`, `numpy`, `librosa`).
- The "Turn-Taking" and "Conversation Progression" sub-metrics are explicitly exposed in the EVA-Bench output format and can be parsed programmatically.
- The dataset (a comprehensive set of scenarios across multiple systems) fits within the available disk limit when including temporary audio files with injected latency..
- The "non-linear failure mode" is expected to manifest as a sharp drop in scores at a specific latency threshold (e.g., 800ms) rather than a gradual linear decline, based on the literature gap analysis.
- The `librosa` or `scipy` libraries used for audio processing are CPU-efficient enough to process the audio chunks within the 6-hour time limit.
- The multiple-comparison correction method (Bonferroni) is appropriate for the number of hypothesis tests being conducted (2 primary metrics).
- The EVA-X "Turn-Taking" metric is either perceptual (independent of raw timing) or the analysis in FR-010 will successfully isolate the non-tautological component of the score.