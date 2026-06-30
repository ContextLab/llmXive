# Feature Specification: DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects

**Feature Branch**: `750-dragmesh-2-reproduction`  
**Created**: 2026-06-21  
**Status**: Draft  
**Input**: User description: "Reproduce & validate: DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects"

## User Scenarios & Testing

### User Story 1 - Environment Setup and Dependency Resolution (Priority: P1)

The researcher MUST be able to instantiate a reproducible execution environment within the GitHub Actions free-tier runner (CPU, limited RAM) that successfully installs all Python dependencies for the vendored `DragMesh-2` codebase without requiring GPU drivers or external internet access beyond package mirrors.

**Why this priority**: Without a functional environment, no validation, training, or evaluation can occur. This is the absolute prerequisite for the reproduction effort.

**Independent Test**: Can be fully tested by executing the `environment.yml` or `requirements.txt` installation script in a clean container and verifying the import of core modules (`pica`, `ppo`, `dataset`) without CUDA errors.

**Acceptance Scenarios**:

1. **Given** a clean GitHub Actions runner with Python 3.9+, **When** the runner executes the dependency installation script, **Then** all packages install successfully without `CUDA_ERROR` or `ImportError` for CPU-only backends.
2. **Given** a completed installation, **When** the user attempts to import `ppo.train` and `pica.a2c_agent`, **Then** the import succeeds and no GPU-specific libraries (e.g., `bitsandbytes` requiring CUDA) are loaded.
3. **Given** a running environment, **When** the system checks available devices, **Then** it reports only CPU devices and successfully initializes the physics simulation backend (e.g., MuJoCo or PyBullet) in CPU mode.

---

### User Story 2 - Training Pipeline Execution (Priority: P2)

The system MUST execute the training loop for the PICA (Physically Informed Contact-Aware) agent on a single articulated object from the GAPartNet dataset using the provided configuration, completing a full training epoch within a reasonable CI time limit on CPU.

**Why this priority**: This validates the core algorithmic claim of the paper (PICA) and ensures the code is not broken. It confirms the method is computationally feasible on the target hardware.

**Independent Test**: Can be fully tested by running `ppo/train.py` with a minimal config for one object and verifying the generation of a checkpoint file and training logs.

**Acceptance Scenarios**:

1. **Given** the `train_config_gla_pica.yaml` and a single GAPartNet object, **When** the training script is executed, **Then** the process completes at least one full epoch without crashing or hanging within 6 hours.
2. **Given** a running training job, **When** the process writes to disk, **Then** a valid PyTorch checkpoint file (`.pt` or `.pth`) is generated containing policy weights.
3. **Given** a completed training run, **When** the training logs are inspected, **Then** they show a monotonically decreasing or stabilizing loss curve and increasing reward signal, indicating learning occurred.

---

### User Story 3 - Evaluation and Robustness Validation (Priority: P3)

The system MUST evaluate the trained policy against multiple damping conditions (contact-load variations) and generate the comparative analysis artifacts (tables/figures) that validate the paper's claim of "stronger robustness under contact-load variation."

**Why this priority**: This directly addresses the paper's primary contribution (robustness) and provides the final evidence required to claim "reproduction complete."

**Independent Test**: Can be fully tested by running the evaluation script against the trained checkpoint across the specified damping range and verifying the output metrics.

**Acceptance Scenarios**:

1. **Given** a trained checkpoint and the evaluation script `scripts/eval/eval_det_stoch_damping.sh`, **When** executed across 7 damping levels, **Then** the system produces a CSV or JSON result file containing success rates for each damping condition.
2. **Given** the evaluation results, **When** the post-processing script `scripts/eval_postprocess.py` is run, **Then** it generates a summary table comparing PICA against the baseline (e.g., trajectory tracking) showing PICA's superior performance in high-damping scenarios.
3. **Given** the final artifacts, **When** the researcher reviews the "work-energy" consistency (as requested by the Feynman reviewer), **Then** the simulation logs or generated visualizations include a specific trace of a single finger-object interaction showing force balance and work calculation over a time step.

---

### Edge Cases

- **What happens when the physics simulation encounters a singular configuration (e.g., finger penetration)?** The system must detect and handle this by either resetting the episode or applying a corrective force, logging the event as a "collision reset" rather than crashing.
- **How does the system handle a training run that exceeds the 6-hour CI limit?** The training script must support checkpointing at regular intervals (e.g., every 10 minutes) and allow resumption from the last checkpoint if the job is preempted or times out.
- **What if the GAPartNet asset files are missing or corrupted?** The system must validate asset integrity at startup and fail fast with a clear error message listing the missing files, rather than failing silently during simulation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST load the `DragMesh-2` codebase from the `external/DragMesh-2` submodule and verify the integrity of all required assets (URDFs, meshes, configs) before execution. (See US-1)
- **FR-002**: System MUST initialize the physics engine (MuJoCo/PyBullet) in CPU-only mode, explicitly disabling any CUDA/GPU acceleration flags. (See US-1)
- **FR-003**: System MUST execute the PICA training loop for a configurable number of iterations, saving intermediate checkpoints to disk at regular intervals. (See US-2)
- **FR-004**: System MUST evaluate the trained policy against a predefined set of damping conditions representing varying contact loads. (See US-3)
- **FR-005**: System MUST generate a comparative analysis report (CSV/JSON) and a visualization artifact (PNG/PDF) showing the success rate of PICA vs. baseline methods across the damping spectrum. (See US-3)
- **FR-006**: System MUST log a specific "force-work" trace for at least one interaction episode, recording normal force, frictional force, and displacement vectors to satisfy the work-energy verification request. (See US-3)

### Key Entities

- **Policy Agent**: The neural network policy trained to control the dexterous hand, storing weights and architecture configuration.
- **Articulated Object**: The target object from GAPartNet with movable joints (e.g., a drawer or door) and variable damping parameters.
- **Damping Condition**: A specific parameter setting for the physics simulation that alters the resistance of the articulated joint, used to test robustness.
- **Interaction Episode**: A single simulation run where the hand attempts to manipulate the object, resulting in a success/failure metric and a trajectory of states.

## Success Criteria

### Measurable Outcomes

> Planning docs state *what* will be measured and the *source/reference* it is measured against; defer specific empirical values (counts, dataset sizes, measured quantities, percentages) to the implementation/research phase.

- **SC-001**: Training time per epoch is measured against the CI job limit to ensure feasibility on free-tier hardware. (See FR-003)
- **SC-002**: Task success rate under high-damping conditions is measured against the baseline trajectory-tracking method to validate the "robustness" claim. (See FR-004, FR-005)
- **SC-003**: Force-work consistency error is measured against the theoretical work-energy theorem (sum of forces * displacement ≈ change in kinetic energy) for the logged interaction episode. (See FR-006)
- **SC-004**: Memory usage peak is measured against the available RAM limit of the GitHub Actions runner to ensure the simulation does not OOM. (See FR-002)
- **SC-005**: The number of successful episodes per damping condition is measured to establish statistical significance of the robustness claim. (See FR-004)

## Assumptions

- The `DragMesh-2` codebase is self-contained within the submodule and does not require external data downloads at runtime beyond the included GAPartNet assets.
- The physics simulation backend (likely MuJoCo) can run in CPU mode with sufficient performance to complete training within 6 hours for a single object.
- The "work-energy" verification requested by the reviewer can be approximated using the simulation's internal force and velocity logs without requiring a custom external physics solver.
- The GAPartNet dataset assets included in the submodule are valid and complete; if not, the reproduction is blocked until asset integrity is restored.
- The GitHub Actions runner environment supports the specific Python version (e.g., 3.9+) and system libraries (e.g., `libgl1`, `libx11`) required by the physics engine.
- The PICA algorithm's hyperparameters in the provided YAML configs are sufficient to achieve convergence on the CPU within the time limit; if not, the scope is limited to demonstrating the pipeline's execution rather than optimal performance.
