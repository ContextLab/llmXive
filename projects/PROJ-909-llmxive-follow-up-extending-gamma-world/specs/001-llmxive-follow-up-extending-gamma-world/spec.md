# Feature Specification: llmXive follow-up: extending "Gamma-World: Generative Multi-Agent World Modeling Beyond Two Players"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-08-26  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Gamma-World: Generative Multi-Agent World Modeling Beyond Two Players' - Research question: Under what structural conditions of agent interaction does non-local information flow become strictly necessary for the emergence of coordinated strategic behaviors in generative world models?"

## User Scenarios & Testing

### User Story 1 - Baseline Model Training and Local Topology Construction (Priority: P1)

**User Journey**: As a researcher, I need to download the Minecraft/RealOmin-Open 4-player datasets and train a "Static-Topo" variant of the Gamma-World model where global attention is replaced by a fixed adjacency matrix based on a 5-meter Euclidean radius, so that I can establish a baseline for local-only coordination capabilities under CPU constraints.

**Why this priority**: This is the foundational step. Without a successfully trained local-only model and a functioning data pipeline that fits within the single-core CPU, 7GB RAM constraints, no comparative analysis can occur. It validates the feasibility of the "local" condition.

**Independent Test**: Can be fully tested by verifying the model trains to completion (50 epochs or early stop) on a sampled subset of the dataset using only a single CPU core, and that the adjacency matrix correctly excludes agents >5m away without crashing due to memory overflow.

**Acceptance Scenarios**:

1. **Given** the Minecraft/RealOmin-Open dataset is downloaded and pre-processed, **When** the Static-Topo model is trained for 50 epochs on a single CPU core runner, **Then** the training completes without out-of-memory (OOM) errors and the adjacency matrix strictly enforces the 5-meter radius constraint.
2. **Given** the Static-Topo model is trained, **When** the model generates video frames for a test episode with agents >5m apart, **Then** the generated frames do not exhibit coordinated strategic behaviors (e.g., flanking, simultaneous attacks) between distant agents that are not explainable by local visual cues alone.

---

### User Story 2 - Complexity Gradient Testing and Behavioral Fidelity Evaluation (Priority: P2)

**User Journey**: As a researcher, I need to systematically vary environmental complexity (agent count, occlusion) and measure the frequency of emergent strategic behaviors (flanking, simultaneous attacks) in both the Local (Static-Topo) and Global (Global-Topo) models, so that I can identify the specific structural threshold where local priors fail to support coordination.

**Why this priority**: This directly addresses the core research question. It moves beyond "can it run" to "where does it break." It requires the successful execution of the inference benchmarking and the behavioral heuristic analysis.

**Independent Test**: Can be fully tested by running the inference benchmark on a held-out test set with varying complexity levels (minimum n ≥ 30 episodes per level) and comparing the frequency of strategic events detected by the ground-truth action log analysis between the two model variants.

**Acceptance Scenarios**:

1. **Given** both Static-Topo and Global-Topo models are trained and ready, **When** they are run on test episodes with increasing agent counts (e.g., 2 to 4) and occlusion levels, **Then** the system records the frequency of strategic behaviors (flanking/attacks) for each model at each complexity level.
2. **Given** the behavioral metrics are collected, **When** the data is analyzed, **Then** a clear divergence point is identified where the frequency of strategic behaviors in the Local model drops significantly below the Global model (e.g., >20% drop) with statistical power ≥ 0.8 and α = 0.05, while the analysis accounts for ground-truth coordination events.

---

### User Story 3 - Statistical Validation and Threshold Sensitivity Analysis (Priority: P3)

**User Journey**: As a researcher, I need to apply a two-way ANOVA to the behavioral frequency data and perform a sensitivity analysis on the distance threshold (e.g., 4m, 5m, 6m) to confirm that the identified "failure point" is robust and not an artifact of the specific 5-meter cutoff choice.

**Why this priority**: This ensures the scientific rigor of the findings. It addresses the "threshold justification" requirement and provides the statistical evidence needed to claim a "structural condition" rather than an observation.

**Independent Test**: Can be fully tested by running the statistical scripts on the collected metrics and verifying that the ANOVA interaction term is significant and that the sensitivity sweep shows a consistent trend around the identified threshold.

**Acceptance Scenarios**:

1. **Given** the behavioral frequency data across complexity levels, **When** a two-way ANOVA is performed (Factors: Model Type, Complexity Level), **Then** the analysis reports a statistically significant interaction effect (p < 0.05) indicating that model performance degrades differently across complexity levels.
2. **Given** the identified failure threshold, **When** the adjacency radius is swept across {4m, 5m, 6m}, **Then** the rate of strategic failure in the Local model shifts predictably, confirming that the 5m boundary is not arbitrary and the threshold is sensitive to geometric constraints.

### Edge Cases

- **What happens when** the dataset lacks sufficient episodes for high-complexity scenarios (e.g., 4 agents with max occlusion)? The system must halt the analysis and generate a "Power Analysis Report" explicitly stating that the threshold could not be determined due to insufficient data (power < 0.8), rather than falling back to a lower complexity level.
- **How does system handle** if the pre-trained action classifier fails to detect a "flanking" maneuver due to occlusion in the generated video? The system must count the event as "undetected" (not false negative) and exclude it from the "successful emergence" metric, ensuring the metric reflects detectable coordination only.
- **What happens when** the CPU memory usage exceeds 7GB during the Global model inference? The system must trigger a fallback to a smaller batch size or a downsampled frame rate, recording the adjustment in the `Assumptions` and `Results` to maintain reproducibility. The fallback algorithm MUST reduce the batch size by 1 iteratively until memory < 7GB, with a minimum batch size of 1.
- **What happens when** the action classifier confidence is ambiguous (e.g., < 0.7)? The system MUST default to the rule-based heuristic fallback to ensure deterministic detection, as specified in FR-005.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and preprocess the Minecraft and RealOmin-Open 4-player datasets, ensuring all necessary variables (agent positions, actions, video frames) are available for training. (See US-1)
- **FR-002**: The system MUST implement a "Static-Topo" model variant where the learnable Sparse Hub Attention is replaced by a fixed adjacency matrix (Static-Topo InteractionGraph) connecting only agents within a 5-meter Euclidean radius. (See US-1)
- **FR-003**: The system MUST train both the Static-Topo and the original Global-Topo models on a single CPU core for a maximum of 50 epochs, utilizing early stopping if convergence is reached. (See US-1)
- **FR-004**: The system MUST systematically vary environmental complexity (agent count, occlusion levels) across test episodes to create a gradient of structural conditions for evaluation. (See US-2)
- **FR-005**: The system MUST quantify emergent strategic behaviors (e.g., flanking, simultaneous attacks) using rule-based heuristics applied to the ground-truth action logs. A "flank" is defined as two agents approaching a target from vectors separated by > 120° within a 2.0s window. A "simultaneous attack" is defined as two agents attacking the same target within a 1.5s window. If ground-truth logs are unavailable for a specific episode, the system MUST fall back to a pre-trained action classifier trained on independent human gameplay data; if classifier confidence is < 0.7, the system MUST default to the rule-based heuristics logic applied to the available video frames. (See US-2)
- **FR-006**: The system MUST apply a two-way ANOVA to compare behavioral frequency metrics between the Local and Global models across manipulated complexity levels to identify interaction effects. If data fails normality tests (Shapiro-Wilk p < 0.05), a GLM with Negative Binomial distribution MAY be used as a secondary check. The analysis MUST test for performance dropping to chance level (p < 0.05 against a random baseline) to validate the claim of "necessity". (See US-3)
- **FR-007**: The system MUST perform a sensitivity analysis sweeping the adjacency distance cutoff over the set {4m, 5m, 6m} to verify the robustness of the identified failure threshold. (See US-3)
- **FR-008**: The system MUST explicitly document that the "Static-Topo" model serves as a lower-bound control for the *capacity* of local coordination, acknowledging that the comparison (Fixed-Local vs. Learned-Global) conflates rigidity and non-locality, and that the research question is scoped to "structural conditions" rather than pure mechanism isolation. This documentation MUST appear in the Discussion section of the final report. (See US-1)
- **FR-009**: The system MUST frame all findings regarding "coordination" as ASSOCIATIONAL unless the experimental design explicitly includes random assignment to interaction topologies; no causal claims regarding "necessity" shall be made without this randomization. (See US-3)
- **FR-010**: The system MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) to all statistical tests performed across the complexity gradient to control the family-wise error rate. (See US-3)
- **FR-011**: The system MUST validate the 5-meter radius choice by computing the median distance of coordinated pairs in the ground-truth dataset and confirming the sensitivity sweep set {4m, 5m, 6m} encompasses this empirical range. If the empirical median is outside this set, the system MUST report this deviation and adjust the sweep range accordingly. (See US-3)
- **FR-012**: The system MUST ensure all model training and inference operations utilize default precision (float32) and strictly avoid any GPU-specific libraries (e.g., CUDA, bitsandbytes, load_in_8bit) to maintain CPU-only feasibility. (See US-1)

### Key Entities

- **AgentState**: Represents the position, velocity, and action of a single agent in the simulation.
- **InteractionGraph**: A dynamic adjacency matrix representing the communication topology (Local vs. Global) for a given episode.
- **Static-Topo**: A specific implementation of the InteractionGraph where connectivity is fixed by a 5-meter Euclidean radius, serving as the local-only baseline.
- **Global-Topo**: The original Gamma-World model variant using a learnable Sparse Hub Attention mechanism, serving as the global-capability baseline.
- **BehavioralMetric**: A quantitative measure (frequency count) of a specific strategic behavior (e.g., "flank_detected") derived from action log analysis.
- **ComplexityLevel**: A categorical or continuous variable representing the environmental difficulty (e.g., "High_Occlusion_4Agents").

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The frequency of emergent strategic behaviors is measured against the ground-truth video frames and independent action classifier outputs to determine the divergence point between Local and Global models. (See US-2)
- **SC-002**: The statistical significance of the interaction between model type and complexity level is measured against the two-way ANOVA results (p-value < 0.05) with a minimum sample size of n ≥ 30 episodes per level to confirm the structural dependency, specifically testing for performance dropping to chance level. (See US-3)
- **SC-003**: The robustness of the failure threshold is measured against the sensitivity analysis results across the distance cutoff set {4m, 5m, 6m} to ensure the finding is not an artifact of a single arbitrary value. (See US-3)
- **SC-004**: The computational feasibility is measured against the single CPU core, 7GB RAM, and 6-hour time limit constraints to ensure the entire analysis pipeline (including data download, preprocessing, training, inference, and statistical analysis) runs without hardware failure. (See US-1)
- **SC-005**: The visual fidelity of the generated videos is measured against FID and SSIM metrics relative to ground-truth frames to ensure that behavioral differences are not due to degradation in video quality. (See US-2)
- **SC-006**: The control of Type I error is measured against the applied multiple-comparison correction method (e.g., adjusted p-values) to ensure the family-wise error rate remains ≤ 0.05 across all hypothesis tests. (See US-3)
- **SC-007**: The validity of the 5m radius assumption is measured against the empirical median distance of coordinated pairs in the ground-truth dataset to ensure the sensitivity analysis range is appropriate. (See US-3)

## Assumptions

- The Minecraft and RealOmin-Open datasets contain the necessary variables (agent positions, actions, video frames) to compute Euclidean distances and train the generative models; if specific variables (e.g., exact occlusion masks) are missing, a proxy metric will be used.
- The "Static-Topo" model variant can be trained within the single CPU core, 7GB RAM constraints by using a sampled subset of the dataset (e.g., [deferred] of full episodes) or by reducing the batch size, without fundamentally altering the structural comparison between local and global attention.
- The rule-based heuristics applied to ground-truth action logs are robust enough to identify strategic behaviors (flanking, simultaneous attacks) even if the video quality is slightly degraded compared to the original dataset.
- The 5-meter radius for the local adjacency matrix is a defensible community-standard default for "local" interaction in multi-agent simulations; the sensitivity analysis will validate if this specific value is critical.
- The two-way ANOVA is the appropriate primary statistical test for this design, as it handles the comparison of means across two factors, with GLM as a fallback for non-normal residuals.
- The "strategic behaviors" detected by the rule-based heuristics are valid proxies for "coordinated strategic behaviors" as defined in the research question, and do not introduce circularity by relying on the model's internal states.
- The research question is scoped to identifying "structural conditions" (local vs. global capacity) rather than isolating the specific mechanism of "learning" the topology, acknowledging the confound in the Fixed-Local vs. Learned-Global comparison.
- The computational constraints (single CPU core, 7GB RAM) are strictly adhered to by the GitHub Actions runner, and no GPU acceleration will be attempted or required for the training or inference steps.
- The sample size of n ≥ 30 episodes per complexity level provides sufficient statistical power (≥ 0.8) to detect the expected interaction effects, assuming the effect size is moderate (Cohen's f ≥ 0.25).
- The ground-truth dataset contains sufficient episodes where coordination actually occurred to serve as the baseline for testing "structural necessity" in the Local model.
- The "Static-Topo" model does not require fine-tuning of the underlying pre-trained weights beyond the attention mask modification, as the base model is assumed to be robust to topological constraints.
- The environmental complexity manipulation (agent count, occlusion) is achievable within the existing dataset structure or via a deterministic sampling strategy that does not require generating new synthetic data.
