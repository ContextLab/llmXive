# Feature Specification: llmXive follow-up: extending "Gamma-World: Generative Multi-Agent World Modeling Beyond Two Players"

**Feature Branch**: `001-llmxive-followup`  
**Created**: 2026-07-11  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'Gamma-World: Generative Multi-Agent World Modeling Beyond Two Players' - Research question: Under what structural conditions of agent interaction does non-local information flow become strictly necessary for the emergence of coordinated strategic behaviors in generative world models?"

## User Scenarios & Testing

### User Story 1 - Baseline Model Training and Local Topology Construction (Priority: P1)

**User Journey**: As a researcher, I need to download the Minecraft/RealOmin-Open 4-player datasets and train a "Static-Topo" variant of the Gamma-World model where global attention is replaced by a fixed adjacency matrix based on a 5-meter Euclidean radius, so that I can establish a baseline for local-only coordination capabilities under CPU constraints.

**Why this priority**: This is the foundational step. Without a successfully trained local-only model and a functioning data pipeline that fits within the 2-core CPU, 7GB RAM constraints, no comparative analysis can occur. It validates the feasibility of the "local" condition.

**Independent Test**: Can be fully tested by verifying the model trains to completion (50 epochs or early stop) on a sampled subset of the dataset using only 2-core CPU resources, and that the adjacency matrix correctly excludes agents >5m away without crashing due to memory overflow.

**Acceptance Scenarios**:

1. **Given** the Minecraft/RealOmin-Open dataset is downloaded and pre-processed, **When** the Static-Topo model is trained for 50 epochs on a 2-core CPU runner, **Then** the training completes without out-of-memory (OOM) errors and the adjacency matrix strictly enforces the 5-meter radius constraint.
2. **Given** the Static-Topo model is trained, **When** the model generates video frames for a test episode with agents >5m apart, **Then** the generated frames do not exhibit coordinated strategic behaviors (e.g., flanking, simultaneous attacks) between distant agents that are not explainable by local visual cues alone.

---

### User Story 2 - Complexity Gradient Testing and Behavioral Fidelity Evaluation (Priority: P2)

**User Journey**: As a researcher, I need to systematically vary environmental complexity (agent count, occlusion) and measure the frequency of emergent strategic behaviors (flanking, simultaneous attacks) in both the Local (Static-Topo) and Global (Sparse Hub) models, so that I can identify the specific structural threshold where local priors fail to support coordination.

**Why this priority**: This directly addresses the core research question. It moves beyond "can it run" to "where does it break." It requires the successful execution of the inference benchmarking and the behavioral heuristic analysis.

**Independent Test**: Can be fully tested by running the inference benchmark on a held-out test set with varying complexity levels (minimum n ≥ 30 episodes per level) and comparing the frequency of strategic events detected by the action classifier (or fallback heuristics) between the two model variants.

**Acceptance Scenarios**:

1. **Given** both Static-Topo and Sparse Hub models are trained and ready, **When** they are run on test episodes with increasing agent counts (e.g., 2 to 4) and occlusion levels, **Then** the system records the frequency of strategic behaviors (flanking/attacks) for each model at each complexity level.
2. **Given** the behavioral metrics are collected, **When** the data is analyzed, **Then** a clear divergence point is identified where the frequency of strategic behaviors in the Local model drops significantly below the Global model (e.g., >20% drop) with statistical power ≥ 0.8 and α = 0.05, while visual fidelity (FID/SSIM) remains comparable.

---

### User Story 3 - Statistical Validation and Threshold Sensitivity Analysis (Priority: P3)

**User Journey**: As a researcher, I need to apply a Generalized Linear Model (GLM) with Negative Binomial distribution to the behavioral frequency data and perform a sensitivity analysis on the distance threshold (e.g., 4m, 5m, 6m) to confirm that the identified "failure point" is robust and not an artifact of the specific 5-meter cutoff choice.

**Why this priority**: This ensures the scientific rigor of the findings. It addresses the "threshold justification" requirement and provides the statistical evidence needed to claim a "structural condition" rather than an observation.

**Independent Test**: Can be fully tested by running the statistical scripts on the collected metrics and verifying that the GLM interaction term is significant and that the sensitivity sweep shows a consistent trend around the identified threshold.

**Acceptance Scenarios**:

1. **Given** the behavioral frequency data across complexity levels, **When** a GLM (Negative Binomial) is performed (Factors: Model Type, Complexity Level), **Then** the analysis reports a statistically significant interaction effect (p < 0.05) indicating that model performance degrades differently across complexity levels.
2. **Given** the identified failure threshold, **When** the adjacency radius is swept across {4m, 5m, 6m}, **Then** the rate of strategic failure in the Local model shifts predictably, confirming that the 5m boundary is not arbitrary and the threshold is sensitive to geometric constraints.

### Edge Cases

- **What happens when** the dataset lacks sufficient episodes for high-complexity scenarios (e.g., 4 agents with max occlusion)? The system must halt the analysis and generate a "Power Analysis Report" explicitly stating that the threshold could not be determined due to insufficient data (power < 0.8), rather than falling back to a lower complexity level.
- **How does system handle** if the pre-trained action classifier fails to detect a "flanking" maneuver due to occlusion in the generated video? The system must count the event as "undetected" (not false negative) and exclude it from the "successful emergence" metric, ensuring the metric reflects detectable coordination only.
- **What happens when** the CPU memory usage exceeds 7GB during the Global model inference? The system must trigger a fallback to a smaller batch size or a downsampled frame rate, recording the adjustment in the `Assumptions` and `Results` to maintain reproducibility.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST download and preprocess the Minecraft and RealOmin-Open 4-player datasets, ensuring all necessary variables (agent positions, actions, video frames) are available for training. (See US-1)
- **FR-002**: The system MUST implement a "Static-Topo" model variant where the learnable Sparse Hub Attention is replaced by a fixed adjacency matrix (Static-Topo InteractionGraph) connecting only agents within a 5-meter Euclidean radius. (See US-1)
- **FR-003**: The system MUST train both the Static-Topo and the original Sparse Hub models on a 2-core CPU for a maximum of 50 epochs, utilizing early stopping if convergence is reached. (See US-1)
- **FR-004**: The system MUST systematically vary environmental complexity (agent count, occlusion levels) across test episodes to create a gradient of structural conditions for evaluation. (See US-2)
- **FR-005**: The system MUST quantify emergent strategic behaviors (e.g., flanking, simultaneous attacks) using a pre-trained action classifier trained on independent human gameplay data. If the classifier confidence score is < 0.7, the system MUST fall back to rule-based heuristics to ensure deterministic detection. (See US-2)
- **FR-006**: The system MUST apply a Generalized Linear Model (GLM) with a Negative Binomial distribution to compare behavioral frequency metrics between the Local and Global models across manipulated complexity levels to identify interaction effects. If data passes normality tests (Shapiro-Wilk p > 0.05), a two-way ANOVA MAY be used as a secondary check. (See US-3)
- **FR-007**: The system MUST perform a sensitivity analysis sweeping the adjacency distance cutoff over the set {4m, 5m, 6m} to verify the robustness of the identified failure threshold. (See US-3)
- **FR-008**: The system MUST validate the action classifier against a "Human-vs-AI" hybrid dataset and report a "Human-Likeness Score". If this score is < 0.6, the system MUST also run a "novel behavior" heuristic to detect non-human-like coordination strategies, preventing false negatives on novel emergence. (See US-2)
- **FR-009**: The system MUST explicitly document that the "Static-Topo" model serves as a lower-bound control for the *capacity* of local coordination, acknowledging that the comparison (Fixed-Local vs. Learned-Global) conflates rigidity and non-locality, and that the research question is scoped to "structural conditions" rather than pure mechanism isolation. (See US-1)

### Key Entities

- **AgentState**: Represents the position, velocity, and action of a single agent in the simulation.
- **InteractionGraph**: A dynamic adjacency matrix representing the communication topology (Local vs. Global) for a given episode.
- **Static-Topo**: A specific implementation of the InteractionGraph where connectivity is fixed by a 5-meter Euclidean radius, serving as the local-only baseline.
- **BehavioralMetric**: A quantitative measure (frequency count) of a specific strategic behavior (e.g., "flank_detected") derived from video analysis.
- **ComplexityLevel**: A categorical or continuous variable representing the environmental difficulty (e.g., "High_Occlusion_4Agents").

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The frequency of emergent strategic behaviors is measured against the ground-truth video frames and independent action classifier outputs (validated for Human-Likeness) to determine the divergence point between Local and Global models. (See US-2)
- **SC-002**: The statistical significance of the interaction between model type and complexity level is measured against the GLM (Negative Binomial) results (p-value < 0.05) with a minimum sample size of n ≥ 30 episodes per level to confirm the structural dependency. (See US-3)
- **SC-003**: The robustness of the failure threshold is measured against the sensitivity analysis results across the distance cutoff set {4m, 5m, 6m} to ensure the finding is not an artifact of a single arbitrary value. (See US-3)
- **SC-004**: The computational feasibility is measured against the 2-core CPU, 7GB RAM, and 6-hour time limit constraints to ensure the entire analysis pipeline runs without hardware failure. (See US-1)
- **SC-005**: The visual fidelity of the generated videos is measured against FID and SSIM metrics relative to ground-truth frames to ensure that behavioral differences are not due to degradation in video quality. (See US-2)
- **SC-006**: The validity of the "emergence" claim is measured against the "Human-Likeness Score" and the "novel behavior" heuristic results to ensure that non-human strategies are not falsely rejected. (See US-2)

## Assumptions

- The Minecraft and RealOmin-Open datasets contain the necessary variables (agent positions, actions, video frames) to compute Euclidean distances and train the generative models; if specific variables (e.g., exact occlusion masks) are missing, a proxy metric will be used.
- The "Static-Topo" model variant can be trained within the 2-core CPU, 7GB RAM constraints by using a sampled subset of the dataset (e.g., [deferred] of full episodes) or by reducing the batch size, without fundamentally altering the structural comparison between local and global attention.
- The pre-trained action classifier used for behavioral detection is robust enough to identify strategic behaviors (flanking, simultaneous attacks) in the generated video frames, even if the video quality is slightly degraded compared to the original dataset.
- The 5-meter radius for the local adjacency matrix is a defensible community-standard default for "local" interaction in multi-agent simulations; the sensitivity analysis will validate if this specific value is critical.
- The Generalized Linear Model (GLM) with Negative Binomial distribution is the appropriate primary statistical test for this design, as it handles count data without violating normality assumptions.
- The "strategic behaviors" detected by the rule-based heuristics or classifier are valid proxies for "coordinated strategic behaviors" as defined in the research question, and do not introduce circularity by relying on the model's internal states.
- The research question is scoped to identifying "structural conditions" (local vs. global capacity) rather than isolating the specific mechanism of "learning" the topology, acknowledging the confound in the Fixed-Local vs. Learned-Global comparison.