# Feature Specification: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Feature Branch**: `001-virtual-tactile-adaptation`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects"

## User Scenarios & Testing

### User Story 1 - Zero-Shot Adaptation to Unseen Damping (Priority: P1)

A researcher simulates a dexterous hand manipulating a novel articulated object (e.g., a stiff drawer) with randomized friction coefficients. The system must automatically detect the physical resistance via the "Virtual Tactile" estimator and dynamically adjust reward weights without any prior training on that specific object.

**Why this priority**: This is the core research hypothesis. If the system cannot adapt to unseen damping conditions, the entire premise of "Virtual Tactile" fails. This is the primary value proposition.

**Independent Test**: Run the adaptive policy on a novel object with a friction coefficient of 1.0 (high friction) where the static baseline fails. Measure the success rate. If the adaptive policy succeeds >15% more often than the static baseline, the core capability is verified.

**Acceptance Scenarios**:

1. **Given** a novel articulated object with randomized friction (0.8–1.2) not seen during training, **When** the agent executes the manipulation task using the adaptive policy, **Then** the system must successfully complete the task (reach goal state) with a frequency at least 15% higher than the static PICA baseline.
2. **Given** a low-friction object (0.1–0.3), **When** the agent executes the task, **Then** the system must maintain stable contact without overshooting, demonstrating that the estimator correctly identifies low stiffness and reduces detachment penalties.

---

### User Story 2 - Virtual Tactile Stiffness Estimation (Priority: P2)

A researcher monitors the internal state of the simulation. The system must compute the stiffness proxy $k_{est}$ in real-time using only the temporal derivative of hand joint torques ($\Delta \tau_{hand}$) and object kinematic error ($\Delta v_{object}$), without requiring external tactile sensors.

**Why this priority**: This is the mechanism enabling User Story 1. Without a valid, computed estimator, the reward scheduler cannot function. It is a prerequisite for the adaptation logic.

**Independent Test**: Inject a known friction value into the simulation, record the torque and velocity derivatives, and verify that the computed $k_{est}$ correlates linearly with the ground-truth friction coefficient across a sweep of multiple randomized trials.

**Acceptance Scenarios**:

1. **Given** a simulation step with non-zero contact forces, **When** the estimator calculates $k_{est} = \frac{|\Delta \tau_{hand}|}{|\Delta v_{object}|}$, **Then** the output must be a finite, positive scalar value within a bounded range (preventing division by zero or NaN).
2. **Given** a sequence of 100 timesteps where friction is artificially increased, **When** the estimator runs, **Then** the adaptive policy utilizing these estimates must achieve a task success rate at least 10% higher than a static-reward baseline policy under the same varying friction conditions.

---

### User Story 3 - CPU-Tractable Inference Pipeline (Priority: P3)

A researcher runs the full training and inference pipeline on a standard GitHub Actions runner. The system must complete the generation of multiple novel object interactions and the statistical comparison of success rates within a feasible time limit and standard RAM constraint, using only CPU resources.

**Why this priority**: This ensures the research is reproducible and feasible within the project's compute budget. If the method requires GPU or exceeds memory, the project cannot reach `research_complete`.

**Independent Test**: Execute the full pipeline (data generation, training, inference, analysis) on a CPU-only runner. Measure total wall-clock time and peak memory usage.

**Acceptance Scenarios**:

1. **Given** a GitHub Actions free-tier runner (2 CPU, 7GB RAM), **When** the full experiment runs, **Then** the job must complete in ≤ 6 hours without OOM (Out of Memory) errors.
2. **Given** the simulation environment, **When** the policy is evaluated, **Then** the system must not invoke any CUDA operations or load quantized (8-bit/4-bit) models that require GPU acceleration.

---

### Edge Cases

- **What happens when** the object velocity $\Delta v_{object}$ is effectively zero (stiction)?
  - The system must apply a small epsilon ($\epsilon = 10^{-4}$) to the denominator to prevent division by zero, ensuring $k_{est}$ remains finite but high, triggering high detachment penalties.
- **How does the system handle** extreme friction values (e.g., 0.0 or >2.0) outside the training distribution?
  - The estimator must clamp the output to a defined range to prevent reward scaling factors from exploding, ensuring simulation stability.
- **What happens if** the torque derivative is noisy due to simulation jitter?
  - The estimator must apply a moving average filter (window size = 5 timesteps) to smooth the $\Delta \tau_{hand}$ signal before computing the ratio.

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the stiffness proxy $k_{est}$ as the ratio of the absolute temporal derivative of hand joint torques to the absolute temporal derivative of object velocity at every simulation timestep in the sliding regime ($|\Delta v_{object}| > 0$), defined as $k_{est} = \frac{|\Delta \tau_{hand}|}{|\Delta v_{object}|}$ (See US-1).
- **FR-002**: System MUST dynamically scale the PICA detachment ($r_{detach}$) and contact maintenance ($r_{contact}$) reward coefficients based on the computed $k_{est}$ value: if $k_{est} > 1.0$, increase $r_{detach}$ by $\ge 20\%$; if $k_{est} < 0.2$, decrease $r_{contact}$ by $\le 15\%$ (See US-1).
- **FR-003**: System MUST generate a diverse set of novel articulated object geometries with randomized friction coefficients (range 0.1 to 1.2) for zero-shot evaluation (See US-1).
- **FR-004**: System MUST perform all physics simulation, policy training, and inference using only CPU resources, prohibiting any CUDA or GPU-accelerated operations (See US-3).
- **FR-005**: System MUST execute a paired t-test comparing the success rates of the adaptive policy against the static PICA baseline across a diverse set of novel objects. (See US-1).
- **FR-006**: System MUST apply a moving average filter (window size = 5) to torque derivative signals to mitigate simulation noise before computing $k_{est}$ (See US-2).
- **FR-007**: System MUST clamp the computed $k_{est}$ value to a physically meaningful positive range bounded by a small lower threshold and a large upper limit. to prevent numerical instability during reward scaling (See Edge Cases).

### Key Entities

- **VirtualTactileEstimator**: A non-neural module that ingests torque and velocity time-series and outputs a scalar stiffness proxy.
- **AdaptiveRewardScheduler**: A heuristic component that maps stiffness proxies to reward weight multipliers.
- **NovelObjectSet**: A collection of 30 generated articulated object geometries with randomized friction properties, distinct from the training set.
- **SimulationEnvironment**: A CPU-based physics engine instance (e.g., PyBullet) configured for dexterous hand manipulation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values to the implementation/research phase.

- **SC-001**: The adaptive policy's success rate on novel high-friction objects must exceed the static PICA baseline success rate by at least 15% (See US-1).
- **SC-002**: The adaptive policy utilizing the estimator must achieve a task success rate at least 10% higher than a static-reward baseline under varying friction conditions (See US-2).
- **SC-003**: The total wall-clock time of the full experiment is measured against the free-tier CI runner's time limit. (See US-3).
- **SC-004**: The peak memory usage during simulation and training is measured against the RAM constraint of the target environment. (See US-3).
- **SC-005**: The paired t-test comparing adaptive vs. static policies must yield a p-value < 0.05 (See US-1).

## Assumptions

- The DragMesh dataset provides sufficient pure-geometry trajectories to serve as a valid base for generating the 30 novel object geometries.
- The PyBullet physics engine (CPU backend) provides sufficient fidelity for torque and velocity derivatives to serve as a valid proxy for contact stiffness in the *sliding regime* (where object velocity is non-zero) for this specific dexterous manipulation context.
- The heuristic scheduler's mapping of $k_{est}$ to reward weights does not require complex hyperparameter tuning beyond the community-standard defaults defined in the implementation.
- The "success rate" metric is defined as the binary outcome of reaching the goal state within the simulation time limit, independent of the intermediate torque values.
- A sample size of novel objects is sufficient to provide a statistically valid sample size for a paired t-test with adequate statistical power given the expected effect size (15-20% improvement).
- The heuristic ratio $|\Delta \tau| / |\Delta v|$ is a valid proxy for contact stiffness only when the object is in motion (sliding), not during stiction, which is handled by the epsilon clamping in FR-007.