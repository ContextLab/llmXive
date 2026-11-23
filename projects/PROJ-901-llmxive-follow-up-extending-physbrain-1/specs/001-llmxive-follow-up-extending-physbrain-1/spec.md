# Feature Specification: llmXive follow-up: extending "PhysBrain 1.0 Technical Report"

**Feature Branch**: `001-kinematic-mismatch-detector`  
**Created**: 2026-07-12  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending 'PhysBrain 1.0 Technical Report'"

## User Scenarios & Testing

### User Story 1 - Pre-execution Kinematic Mismatch Detection (Priority: P1)

A safety engineer or autonomous system operator needs to screen incoming action descriptions (e.g., "hold cup with two hands") against a specific robot's kinematic model to determine if the action is physically feasible before execution.

**Why this priority**: This is the core value proposition. Without this filter, the system risks catastrophic failure or resource waste by attempting human-centric actions on non-humanoid hardware. It directly addresses the research question regarding the degradation of linguistic priors.

**Independent Test**: The system can be tested by feeding a curated list of known mismatched and matched text descriptions into the classifier. The ground truth for these 100 examples must be manually curated with a minimum inter-annotator agreement (Cohen's Kappa) of ≥0.8 to ensure independence from the training simulation. The output binary flag must correctly identify the mismatch with ≥85% precision against this independent gold standard.

**Acceptance Scenarios**:
1. **Given** a text description of an action requiring two dexterous hands and a robot with a single rigid gripper, **When** the description is processed by the detector, **Then** the system outputs a "mismatch" flag with a confidence score > 0.8.
2. **Given** a text description of a simple grasping action compatible with a single gripper and a robot with a single rigid gripper, **When** the description is processed, **Then** the system outputs a "safe" flag.
3. **Given** a text description with high kinematic divergence (e.g., "wrist rotation beyond 180 degrees") and a robot with a rigid arm, **When** processed, **Then** the system flags the mismatch and prevents the simulation from initiating the high-risk action.

---

### User Story 2 - CPU-Tractability & Latency Verification (Priority: P2)

A deployment engineer needs to ensure the mismatch detector runs within strict resource constraints (≤7 GB RAM, ≤600ms latency) on a standard CPU-only CI runner to be viable for real-time safety filtering.

**Why this priority**: The motivation explicitly states the need for a "lightweight, CPU-tractable detector." If the model requires GPU or excessive RAM, the safety layer cannot be deployed in the target environment, rendering the research moot for real-world robotics.

**Independent Test**: The trained model artifact can be loaded and run through a stress test of [deferred] inferences on a standard 2-core CPU instance; the test passes if average latency is < 600ms and peak memory usage remains < 7 GB.

**Acceptance Scenarios**:
1. **Given** a standard GitHub Actions runner environment (2 CPU, 7 GB RAM, no GPU), **When** the detector model is loaded and [deferred] inference requests are processed, **Then** the average inference time is ≤ 600ms and peak RAM usage is ≤ 7 GB.
2. **Given** a request during a CI pipeline execution, **When** the detector is invoked, **Then** the total job duration increases by no more than 5 minutes compared to a baseline run without the detector.

---

### User Story 3 - Statistical Significance of Safety Improvement (Priority: P3)

A researcher needs to validate that using the detector significantly reduces collision rates or control instability compared to a baseline where the detector is absent.

**Why this priority**: This validates the "Expected results" claim (>85% precision leading to improved safety). It moves the project from a theoretical classifier to an empirically proven safety mechanism.

**Independent Test**: The system can be tested by running a fixed set of 500 simulation tasks (40% mismatched, [deferred] matched, [deferred] edge-case) from the dataset `data/kinematic_validation_v1.json` with and without the detector enabled. The validation compares the detector's *predictions* against the physics engine's collision logs of the *original* (non-fallback) action to confirm statistical significance (p < 0.05) in prediction accuracy.

**Acceptance Scenarios**:
1. **Given** a dataset of 500 simulated tasks involving potential kinematic mismatches, **When** the detector is enabled, **Then** the detector's prediction of "mismatch" matches the physics engine's ground-truth collision log for the original action with a statistically significant accuracy (p < 0.05) compared to a random baseline.
2. **Given** a set of tasks where the detector flags a mismatch, **When** the system switches to the fallback controller, **Then** the fallback controller successfully completes the task or terminates safely without collision in ≥90% of cases.

---

### User Story 4 - Multiple-Comparison Correction (Priority: P3)

A researcher needs to ensure that statistical claims regarding safety improvements across multiple robot configurations do not suffer from Type I error inflation due to multiple hypothesis testing.

**Why this priority**: When evaluating performance across N different robot configurations, performing N independent tests without correction inflates the false positive rate. This requirement ensures scientific rigor in the final report.

**Independent Test**: The system MUST automatically apply a Benjamini-Hochberg correction when generating the final statistical report for >1 robot configuration. The test passes if the reported p-values are adjusted and the corrected significance threshold is applied.

**Acceptance Scenarios**:
1. **Given** a report generation request for 5 different robot configurations, **When** the statistical analysis is run, **Then** the system applies the Benjamini-Hochberg procedure and reports the adjusted p-values.
2. **Given** a set of uncorrected p-values [0.01, 0.03, 0.06], **When** the correction is applied with α=0.05, **Then** the system correctly identifies which hypotheses remain significant after adjustment.

### Edge Cases

- What happens when the input text description is ambiguous (e.g., "hold object") without specifying the number of hands or grip type?
- How does the system handle a robot configuration that is a hybrid (e.g., humanoid torso but wheeled base) where some actions match and others do not?
- What is the behavior if the physics engine logs (ground truth) are missing or corrupted for a test case?

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse text-based action descriptions and spatial relation tags to extract structured feature vectors suitable for a lightweight classifier (See US-1).
- **FR-002**: System MUST classify input descriptions as either "kinematic match" or "kinematic mismatch" based on a trained binary classifier (See US-1).
- **FR-003**: System MUST execute the classification model on a CPU-only environment without requiring CUDA, GPU accelerators, or 8-bit/4-bit quantization libraries, ensuring peak RAM usage ≤7 GB (See US-2).
- **FR-004**: System MUST log the inference latency and peak memory usage for every batch of predictions to verify resource constraints (See US-2).
- **FR-005**: System MUST compare the prediction accuracy of the detector against the independent ground truth (physics engine logs of original actions) using a paired statistical test (e.g., McNemar's test) and report the p-value (See US-3).
- **FR-006**: System MUST apply a multiple-comparison correction (e.g., Bonferroni or Benjamini-Hochberg) if more than one hypothesis test is performed across different robot configurations (See US-4).

### Key Entities

- **ActionDescription**: A text string representing a physical task (e.g., "open door with handle") and associated spatial tags.
- **KinematicProfile**: A structured representation of a robot's physical constraints (degrees of freedom, joint limits, end-effector type).
- **MismatchFlag**: A binary output (0/1) or probability score indicating the likelihood of a kinematic violation.
- **SimulationLog**: The ground truth data from the physics engine (e.g., collision count, success/failure status) used for validation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is
> measured against; defer specific empirical values (counts, dataset sizes,
> measured quantities, percentages) to the implementation/research phase.

- **SC-001**: The precision of the mismatch detector is measured against the held-out test set of SimplerEnv and RoboCasa tasks where kinematic divergence is known (See FR-002).
- **SC-002**: The inference latency (ms) and peak RAM usage (GB) are measured against the GitHub Actions free-tier constraints (2 CPU, 7 GB RAM) (See FR-003).
- **SC-003**: The reduction in collision rates (or increase in safety success rate) is measured against the baseline collision rate of the same tasks executed without the detector (See FR-005).
- **SC-004**: The statistical significance of the safety improvement is measured against a p-value threshold of 0.05 using a paired test (See FR-005).
- **SC-005**: The sensitivity of the detection threshold is measured by sweeping the decision cutoff over a range of {0.01, 0.05, 0.1} and reporting the variation in False-Positive Rate (FPR) and False-Negative Rate (FNR) (See FR-006).

## Assumptions

- The PhysBrain training corpus contains sufficient examples of actions with high kinematic divergence to train a binary classifier (if not, synthetic data generation via SimplerEnv/RoboCasa is assumed to be feasible within the 6-hour compute budget).
- The "kinematic mismatch" ground truth can be reliably derived from the physics engine's collision logs or success/failure flags in SimplerEnv and RoboCasa without manual annotation.
- The dataset variables (text descriptions, spatial tags, simulation outcomes) are fully available and do not require external, unverified data sources; specifically, the pipeline to generate structured text-action pairs and their corresponding kinematic failure labels from the PhysBrain/SimplerEnv corpus is included in the scope.
- The chosen lightweight classifier (e.g., Decision Tree or shallow MLP) is sufficient to capture the non-linear relationships between semantic text and kinematic failure modes.
- The threshold for classifying a "mismatch" will be set to 0.5 by default, with a sensitivity analysis performed to justify any deviation from this standard.
- The research design is observational; findings regarding the degradation of priors will be framed as associational unless the idea explicitly specifies a randomized intervention strategy.
- The sample size for the validation set is [deferred] but will be calculated based on a power analysis to ensure the McNemar's test has sufficient power (≥0.8) to detect a meaningful difference in error rates.
- **Simulation-Consistency Assumption**: The validation metric measures "simulation-consistency" (the detector's ability to predict the physics engine's outcome) rather than "physical feasibility" in the real world, acknowledging that the ground truth is defined by the simulation engine's collision/failure outcome.