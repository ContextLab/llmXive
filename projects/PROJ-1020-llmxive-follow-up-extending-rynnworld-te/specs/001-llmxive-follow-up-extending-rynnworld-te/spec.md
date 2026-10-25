# Feature Specification: Minimum Visual Fidelity Threshold for Sim2Real Transfer in Digital Teleoperation

**Feature Branch**: `001-llmxive-follow-up-extending-rynnworld-te`  
**Created**: 2026-10-25  
**Status**: Draft  
**Input**: User description:  

> What is the minimum visual fidelity threshold in action‑conditioned world models required to maintain robust Sim2Real transfer for robotic teleoperation, and which specific perceptual features are critical when high‑fidelity video synthesis is unavailable? The project will train lightweight recurrent models on three observation streams (full‑resolution video, low‑fidelity downsampled video, and sparse latent vectors containing object centroids & kinematic states) derived from the RynnWorld‑Teleop dataset, generate synthetic trajectories, train imitation‑learning policies on each, and evaluate task success rates in a CPU‑only PyBullet simulation. A feature‑ablation study will identify which latent components are essential for transfer.

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Quantify Fidelity‑Performance Trade‑off (Priority: P1)

A researcher wants to know how reducing visual fidelity impacts the success rate of policies trained on synthetic data, so they can decide whether a CPU‑only latent representation is sufficient for edge deployment.

**Why this priority**: Establishes the core scientific contribution—identifying the “fidelity cliff”—and determines the feasibility of scaling digital teleoperation without GPUs.

**Independent Test**: Run the full experimental pipeline for a single fidelity level (e.g., Sparse latent) and verify that a measurable task‑success rate is produced and reported.

**Acceptance Scenarios**:

1. **Given** the RynnWorld‑Teleop dataset, a pipeline that extracts sparse latent vectors (object centroids + kinematic states) and trains a GRU world model on CPU, **When** synthetic trajectories are generated and an imitation‑learning policy is trained on them, **Then** the policy’s task‑success rate in PyBullet is reported as a percentage.

2. **Given** the same dataset and the low‑fidelity downsampled‑video stream, **When** the identical training and evaluation steps are executed, **Then** the resulting task‑success rate is compared against the full‑video baseline and the difference is quantified.

### User Story 2 – Identify Critical Perceptual Features (Priority: P2)

A robotics engineer needs to know which components of the sparse latent vector (e.g., contact states, object centroids) are indispensable for Sim2Real transfer, so they can design minimal perception modules for edge robots.

**Why this priority**: Provides actionable design guidance for future low‑resource teleoperation systems.

**Independent Test**: Perform a systematic ablation where each latent component is masked or corrupted, retrain the policy, and measure the resulting success rate.

**Acceptance Scenarios**:

1. **Given** a trained sparse‑latent policy, **When** the contact‑state dimensions are zeroed out for all synthetic trajectories, **Then** the policy’s success rate drops below 80 % of the full‑video baseline.

### User Story 3 – Demonstrate CPU‑Only Feasibility (Priority: P3)

A system integrator wants evidence that the entire pipeline (data processing, model training, policy inference) runs within the resource limits of a free‑tier GitHub Actions runner.

**Why this priority**: Guarantees reproducibility and deployability of the research without specialized hardware.

**Independent Test**: Execute the full pipeline on a CI runner and log peak RAM usage, total CPU‑seconds, and wall‑clock time; all must stay ≤ 7 GB RAM, ≤ 14 GB disk, and ≤ 6 h runtime.

**Acceptance Scenarios**:

1. **Given** the CI environment, **When** the GRU world model is trained on the sparse latent stream (using a sampled [deferred] of the dataset), **Then** peak RAM ≤ 6.5 GB, total CPU‑seconds ≤ 30 000 s, and wall‑clock time ≤ 5 h 45 min.

### Edge Cases

- **Boundary Condition**: What happens if the latent vector is missing the object‑centroid component entirely?
- **Error Scenario**: How does the pipeline react when the YOLO‑Nano detector fails to detect any objects in a frame?
- **Data Scarcity**: How is performance affected if only [deferred] of the original dataset is used for training due to storage limits?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001** (See US-1): System MUST extract three observation streams from the RynnWorld‑Teleop dataset – full‑resolution video, downsampled low‑fidelity video, and sparse latent vectors containing object centroids and kinematic states.  
- **FR-002** (See US-1): System MUST train a CPU‑only GRU world model on each observation stream, using INT8 quantized weights and a batch size that fits ≤ 7 GB RAM.  
- **FR-003** (See US-1): System MUST generate synthetic trajectories by rolling out each trained GRU from random initial conditions and recorded action sequences.  
- **FR-004** (See US-1): System MUST train an imitation‑learning policy (ACT architecture) on each synthetic dataset, consuming only the corresponding observation stream as input.  
- **FR-005** (See US-1): System MUST evaluate each policy in a deterministic PyBullet simulation and record the task‑success rate (percentage of successful object manipulations).  
- **FR-006** (See US-2): System MUST perform a systematic feature‑ablation study on the sparse latent vector, masking each component (centroids, contact states, joint angles) independently and reporting the resulting success‑rate change.  
- **FR-007** (See US-3): System MUST log resource usage (peak RAM, total CPU‑seconds, wall‑clock time) for each pipeline stage and enforce the limits: RAM ≤ 7 GB, CPU‑seconds ≤ 30 000 s, wall‑clock ≤ 6 h.  
- **FR-008** (See US-1): System MUST apply a family‑wise error rate correction (Bonferroni) to all hypothesis tests arising from the ANOVA and post‑hoc t‑tests.  
- **FR-009** (See US-1): System MUST conduct a sensitivity analysis over the fidelity‑reduction thresholds: (a) video downsampling factors {2×, 4×, 8×}; (b) latent‑vector noise levels {σ = 0.01, 0.05, 0.1}. Results must be reported as variation in success rate.  
- **FR-010** (See US-1): System MUST produce a reproducible results package containing: (i) raw success‑rate tables, (ii) statistical test outputs, (iii) resource‑usage logs, and (iv) the code version hash.

### Key Entities

- **RynnWorld‑Teleop Dataset** – Collection of paired robot‑action sequences and high‑fidelity video recordings.  
- **Sparse Latent Vector** – Fixed‑length numeric representation per timestep composed of: object centroids (x, y), object orientation (θ), robot joint angles, and binary contact flags.  
- **GRU World Model** – Recurrent neural network predicting next latent state given current state and hand‑pose action.  
- **Imitation‑Learning Policy** – ACT (Action Chunking with Transformers) model that maps observations to robot actions.  

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001** (See US-1): The Sparse‑latent policy achieves ≥ 85 % of the Full‑video baseline success rate (i.e., if baseline = 90 %, sparse ≥ 76.5 %).  
- **SC-002** (See US-1): The Low‑fidelity video policy achieves ≥ 80 % of the Full‑video baseline success rate.  
- **SC-003** (See US-2): Masking any *critical* latent component (identified by the ablation) reduces the policy’s success rate below 80 % of baseline, confirming its necessity.  
- **SC-004** (See US-3): All pipeline stages complete within the resource limits specified in FR‑007 on a free‑tier GitHub Actions runner.  
- **SC-05** (See US-1): Statistical analysis reports a significant main effect of fidelity level on success rate (p < 0.05 after Bonferroni correction).  
- **SC-06** (See US-1): Sensitivity analysis shows that success‑rate variation across the specified fidelity thresholds is ≤ 5 % absolute, demonstrating robustness of the identified “fidelity cliff”.  

## Assumptions

- The RynnWorld‑Teleop dataset includes accurate timestamps and synchronized robot‑action logs required to align observations with actions.  
- A frozen YOLO‑Nano model can reliably detect the relevant objects in the video frames; detection failures are rare (< 2 % of frames).  
- Contact states can be estimated heuristically from object motion (e.g., sudden velocity changes) without ground‑truth labels. **[NEEDS CLARIFICATION: Does the dataset provide explicit contact annotations?]**  
- The CPU‑only environment provides a Python 3.11 runtime with `numpy`, `torch` (CPU‑only), `scikit‑learn`, `pybullet`, and `opencv` pre‑installed.  
- Training on a modest random subset of the dataset is sufficient to reach stable convergence for GRU models; larger subsets would not materially change the fidelity‑performance curve.  

---
