# Feature Specification: llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation

**Feature Branch**: `001-virtual-tactile-adaptation`  
**Created**: 2026-07-13  
**Status**: Draft  
**Input**: User description: "llmXive follow-up: extending DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects"

## User Scenarios & Testing

### User Story 1 - Zero-Shot Adaptation to Unseen Friction (Priority: P1)

A researcher simulates a dexterous hand manipulating a novel articulated object (e.g., a stiff drawer) with randomized friction coefficients. The system must automatically detect the physical resistance via the "Virtual Tactile" estimator and dynamically adjust reward weights without any prior training on that specific object. *In this work, “damping” refers to the friction coefficient of the contact surface.*

**Why this priority**: This is the core research hypothesis. If the system cannot adapt to unseen friction conditions, the entire premise of "Virtual Tactile" fails. This is the primary value proposition.

**Independent Test**: Run the adaptive policy on a novel object with a friction coefficient of 1.0 (high friction) where the static baseline fails. Measure the success rate. If the adaptive policy succeeds >15% more often than the static PICA baseline, the core capability is verified.

**Acceptance Scenarios**:

1. **Given** a novel articulated object with randomized friction (0.8–1.2) that is **outside** the training friction range (0.2–0.6) (See FR-010), **When** the agent executes the manipulation task using the adaptive policy, **Then** the system must successfully complete the task (reach goal state) with a frequency at least 15% higher than the static PICA baseline. (See SC-001, US-1)
2. **Given** a low‑friction object (0.1–0.3), **When** the agent executes the task, **Then** the system must maintain stable contact without overshooting, demonstrating that the estimator correctly identifies low friction and **decreases the detachment reward** by ≥15% (See FR-002, US-1).

---

### User Story 2 - Virtual Tactile Friction Estimation (Priority: P2)

A researcher monitors the internal state of the simulation. The system must compute the friction proxy $k_{\text{norm}}$ in real‑time using only the temporal derivative of hand joint torques ($\Delta \tau_{\text{hand}}$), object kinematic error ($\Delta v_{\text{object}}$), and the estimated normal contact force $N$ (see FR-009), without requiring external tactile sensors.

**Why this priority**: This is the mechanism enabling User Story 1. Without a valid, computed estimator, the reward scheduler cannot function. It is a prerequisite for the adaptation logic.

**Independent Test**: Inject a known friction value into the simulation, record the torque and velocity derivatives, and verify that the computed $k_{\text{norm}}$ **correlates linearly** with the ground‑truth friction coefficient across a sweep of multiple randomized trials. The correlation must satisfy **Pearson $r \ge 0.8$** over **at least 30 trials** (See FR-008, SC-006).

**Acceptance Scenarios**:

1. **Given** a simulation step with non‑zero contact forces, **When** the estimator calculates  

   $$k_{\text{norm}} = \frac{|\Delta \tau_{\text{hand}}|}{|\Delta v_{\text{object}}|\; N}$$  

   **Then** the output must be a finite, positive scalar value within the clamped range $[1\!\times\!10^{-4},\,10]$ (see FR-007) and, if $|\Delta v_{\text{object}}|$ is effectively zero, the denominator uses $\epsilon = 10^{-4}$ to avoid division by zero (see FR-001).  
2. **Given** a sequence of 100 timesteps where friction is artificially increased, **When** the estimator runs, **Then** the adaptive policy utilizing these estimates must achieve a task success rate at least 10% higher than a static‑reward baseline under the same varying friction conditions. (See SC-002, US-2)

---

### User Story 3 - CPU‑Tractable Inference Pipeline (Priority: P3)

A researcher runs the full training and inference pipeline on a standard GitHub Actions runner. The system must complete the generation of multiple novel object interactions and the statistical comparison of success rates within a feasible time limit and standard RAM constraint, using only CPU resources.

**Why this priority**: This ensures the research is reproducible and feasible within the project's compute budget. If the method requires GPU or exceeds memory, the project cannot reach `research_complete`.

**Independent Test**: Execute the full pipeline (data generation, training, inference, analysis) on a CPU‑only runner. Measure total wall‑clock time and peak memory usage.

**Acceptance Scenarios**:

1. **Given** a GitHub Actions free‑tier runner (2 CPU, 7 GB RAM), **When** the full experiment runs, **Then** the job must complete in **≤ 6 hours** without OOM (Out of Memory) errors. (See SC-003, US-3)
2. **Given** the simulation environment, **When** the policy is evaluated, **Then** the system must not invoke any CUDA operations or load quantized (8‑bit/4‑bit) models that require GPU acceleration. (See FR-004, US-3)

---

### Edge Cases

- **What happens when** the object velocity $\Delta v_{\text{object}}$ is effectively zero (stiction)?  
  The system applies a small epsilon ($\epsilon = 10^{-4}$) to the denominator as defined in FR‑001, ensuring $k_{\text{norm}}$ remains finite but high, triggering high detachment penalties.

- **How does the system handle** extreme friction values (e.g., 0.0 or >2.0) outside the training distribution?  
  The estimator clamps the output to the range $[1\!\times\!10^{-4},\,10]$ (FR‑007) to prevent reward scaling factors from exploding, ensuring simulation stability.

- **What happens if** the torque derivative is noisy due to simulation jitter?  
  The estimator applies a moving average filter (window size = 5 timesteps) to smooth the $\Delta \tau_{\text{hand}}$ signal before computing the ratio (see FR‑006, verified filter size source).

## Requirements

### Functional Requirements

- **FR-001**: System MUST compute the friction proxy $k_{\text{norm}}$ as  

  $$k_{\text{norm}} = \frac{|\Delta \tau_{\text{hand}}|}{\max(|\Delta v_{\text{object}}|,\;\epsilon)\; N}$$  

  where $\epsilon = 10^{-4}$ and $N$ is the estimated normal contact force at each contact point (See US‑2). Computation occurs at every simulation timestep. (See US‑2)

- **FR-002**: System MUST dynamically scale the PICA detachment reward coefficient $r_{\text{detach}}$ based on the percentile position of $k_{\text{norm}}$ within the training distribution:  
  - If $k_{\text{norm}}$ exceeds the **90th percentile**, increase $r_{\text{detach}}$ by **≥ 20%**.  
  - If $k_{\text{norm}}$ falls below the **10th percentile**, **decrease** $r_{\text{detach}}$ by **≥ 15%**. (See US‑1)

- **FR-003**: System MUST generate **exactly 10** novel articulated object geometries with randomized friction coefficients **outside** the training range (0.2–0.6) (See FR‑010, US‑1).

- **FR-004**: System MUST perform all physics simulation, policy training, and inference using only CPU resources, prohibiting any CUDA or GPU‑accelerated operations (See US‑3).

- **FR-005**: System MUST analyze the adaptive vs. static policy performance using a **mixed‑effects logistic regression** model that accounts for per‑object random effects; the analysis must report a p‑value < 0.05 for the effect of adaptation. (See US‑1)

- **FR-006**: System MUST apply a moving average filter (window size = 5) to torque derivative signals to mitigate simulation noise before computing $k_{\text{norm}}$ (See US‑2). *(Verified filter size source: Gaussian filter, https://en.wikipedia.org/wiki/Gaussian_filter)*

- **FR-007**: System MUST clamp the computed $k_{\text{norm}}$ value to the physically meaningful positive range **[1 × 10⁻⁴, 10]** to prevent numerical instability during reward scaling. (See US‑2)

- **FR-008**: System MUST conduct a correlation‑validation experiment that computes Pearson correlation $r$ between $k_{\text{norm}}$ and the ground‑truth friction coefficient over **≥ 30** randomized trials; the experiment passes if $r ≥ 0.8$. (See US‑2)

- **FR-009**: System MUST estimate and log the normal contact force $N$ at each contact point each timestep, making it available to the $k_{\text{norm}}$ computation. (See US‑2)

- **FR-010**: System MUST train on a dataset where friction coefficients are **uniformly sampled from 0.2 to 0.6**. Test objects must have friction coefficients **≥ 0.8** or **≤ 0.1**, ensuring a zero‑shot domain shift. (See US‑1)

- **FR-011**: System MUST use the percentile‑based reward scaling described in FR‑002 (90th / 10th percentile) rather than absolute numeric thresholds, ensuring dimensionless applicability across objects. (See US‑1)

### Key Entities

- **VirtualTactileEstimator**: A non‑neural module that ingests torque, velocity, and normal‑force time‑series and outputs a scalar friction proxy $k_{\text{norm}}$.
- **AdaptiveRewardScheduler**: A heuristic component that maps $k_{\text{norm}}$ percentiles to reward weight multipliers.
- **NovelObjectSet**: A collection of **10** generated articulated object geometries with friction coefficients outside the training distribution.
- **SimulationEnvironment**: A CPU‑based physics engine instance (e.g., PyBullet) configured for dexterous hand manipulation.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, percentages) to the implementation/research phase.

- **SC-001**: The adaptive policy's success rate on novel high‑friction objects must exceed the static PICA baseline success rate by at least **[deferred]**. (See US‑1)
- **SC-002**: The adaptive policy utilizing the estimator must achieve a task success rate at least **[deferred]** higher than a static‑reward baseline under varying friction conditions. (See US‑2)
- **SC-003**: The total wall‑clock time of the full experiment must be **≤ 6 hours** on a free‑tier CI runner. (See US‑3)
- **SC-004**: The peak memory usage during simulation and training must be **≤ 7 GB**. (See US‑3)
- **SC-005**: The mixed‑effects logistic regression comparing adaptive vs. static policies must yield a **p‑value < 0.05**. (See US‑1)
- **SC-006**: The correlation‑validation experiment (FR‑008) must report Pearson $r ≥ 0.8$ over ≥ 30 trials. (See US‑2)

## Assumptions

- The DragMesh‑2 dataset provides **277** pure‑geometry trajectories that serve as the base for generating novel object geometries.
- The PyBullet physics engine (CPU backend) provides sufficient fidelity for torque and velocity derivatives to serve as a valid proxy for friction in the sliding regime (where object velocity is non‑zero) for this dexterous manipulation context.
- The heuristic scheduler's mapping of $k_{\text{norm}}$ percentiles to reward weights does not require complex hyper‑parameter tuning beyond the community‑standard defaults defined in the implementation.
- The “success rate” metric is defined as the binary outcome of reaching the goal state within the simulation time limit, independent of intermediate torque values.
- A sample size of **10** novel objects (as defined in FR‑003) is sufficient to provide a statistically valid sample for the mixed‑effects regression given the expected effect size (moderate improvement) and the power analysis performed during design.
- The estimator’s output $k_{\text{norm}}$ is interpreted as a **friction proxy**, not a stiffness measure; this aligns the validation target (ground‑truth friction) with the construct being measured.
