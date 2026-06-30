# Research: DragMesh-2: Physically Plausible Dexterous Hand-Object Interaction with Articulated Objects

## Summary

This research phase validates the feasibility of reproducing the DragMesh-2 PICA agent on a CPU-only CI environment. It confirms the availability of the GAPartNet dataset, identifies the necessary physics engine configuration for CPU execution, and outlines the strategy for the "work-energy" verification requested by the Feynman reviewer, ensuring all energy terms are explicitly accounted for.

## Dataset Strategy

The project relies on the **GAPartNet** dataset for articulated object assets.

| Dataset Name | Verified Source (URL) | Usage in Plan |
|:--- |:--- |:--- |
| **GAPartNet Metadata** | ` | Provides the split definitions and metadata for selecting a single articulated object (e.g., drawer) for the reproduction run. |
| **Physical Assets (URDFs/Meshes)** | *Included in `external/DragMesh-2/assets/` (Submodule)* | The actual physics assets required for simulation. **Critical Note**: The plan does NOT assume these are present. A mandatory "Asset Integrity Check" (FR-001) will verify the existence of URDF files in the submodule. If missing, the build fails with a clear error. |

*Note: If the JSON file does not contain direct links to the physical assets, the plan relies on the submodule. If the submodule is incomplete, the reproduction is blocked until assets are restored.*

## Technical Feasibility & Compute Constraints

### Physics Engine: CPU-Only Mode
The spec requires running on a GitHub Actions runner (2 CPU, 7 GB RAM, no GPU).
- **Decision**: Use **MuJoCo** in strict CPU mode.
- **Rationale**: MuJoCo is the standard for the DragMesh paper. It supports CPU execution. We must explicitly disable any CUDA flags in the build configuration.
- **Constraint**: No `load_in_8bit` or CUDA-specific optimizations. The PPO/PICA agent will run on `torch.device('cpu')`.
- **Risk**: Training time.
- **Mitigation**: The plan limits training to a **single object** and a **reduced step count** (sampled) to ensure completion within 6 hours. If the original paper used 1M steps, we will target ~50k-100k steps for the reproduction demo, explicitly noting this as a "feasibility demonstration" rather than a full performance benchmark.

### Memory Management
- **Constraint**: 7 GB RAM limit.
- **Strategy**:
 - Load only one object instance into the physics engine at a time.
 - Use a small batch size for PPO (e.g., 64 or 128).
 - Disable verbose logging of full trajectory buffers to disk; only log aggregated stats and the specific "work-energy" trace (FR-006).
 - Garbage collection forced every N episodes.

## Methodological Rigor & Statistical Considerations

### Robustness Validation (FR-004, SC-002)
The plan evaluates the agent against **7 damping levels**.
- **Method**: Run multiple independent episodes per damping level.
- **Metric**: Success rate (binary) and final displacement error.
- **Statistical Note**: With N=10-20 per condition, statistical power is low. The plan will report **confidence intervals** (Wilson score interval) for success rates.
 - **Definition of "Robustness Trend"**: A trend is considered "meaningful" only if the 95% confidence intervals of PICA and the Baseline do not overlap at high damping levels. If CIs overlap, results are framed as "preliminary feasibility" or "inconclusive" rather than "superiority."
- **Baseline**: The baseline (trajectory tracking) must be run with the **same domain randomization** during training to ensure a fair comparison.

### Work-Energy Verification (FR-006, SC-003)
This addresses the Feynman reviewer's request for a "simple, concrete example with numbers."
- **Method**: During a single representative episode (steady motion phase), log:
 1. `t`: Time step.
 2. `F_normal`: Normal force vector magnitude.
 3. `F_friction`: Frictional force vector magnitude.
 4. `F_gravity`: Gravity force vector magnitude.
 5. `v_finger`: Finger tip velocity vector.
 6. `v_object`: Object contact point velocity vector.
 7. `damping_torque`: Joint damping torque.
- **Calculation**:
 - Work done by finger: $W_{finger} = \int (F_{finger} \cdot v_{finger}) dt$
 - Change in Kinetic Energy: $\Delta KE = KE_{t+1} - KE_t$
 - Change in Potential Energy: $\Delta PE = m \cdot g \cdot \Delta h$
 - Dissipation Work: $W_{diss} = \int (F_{friction} \cdot v_{rel}) dt + \int (\tau_{damping} \cdot \omega) dt$
 - **Energy Balance Check**: $W_{finger} \approx \Delta KE + \Delta PE + W_{diss}$
 - **Error Metric**: $Error = |W_{finger} - (\Delta KE + \Delta PE + W_{diss})|$
- **Output**: A CSV/JSON file with these columns and a generated plot (PNG) showing the force vectors and the work balance over time.
- **Clarification**: This check validates the **simulation engine's internal consistency** and the **logging implementation**. A non-zero error indicates a bug in the physics engine or logging, not necessarily a failure of the agent. The agent's "physical plausibility" is validated by the **robustness results** (FR-004).

### Convergence Criterion
- **Requirement**: To avoid false negatives from under-training, the training loop will check for convergence.
- **Criterion**: Reward plateau (change < 1% steps) OR hard cap at [deferred] steps.
- **Flagging**: If the hard cap is reached without plateau, the run is flagged as "non-converged" in the results. The robustness evaluation will still proceed, but results will be interpreted as "partial reproduction" rather than full validation.

## Risk Analysis

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Physics Engine OOM** | Crash > 7 GB RAM | Limit object complexity (use simplified meshes); reduce batch size. |
| **Training Timeout** | Job > 6 hours | Hard limit on steps; checkpoint every 5 mins; fail-fast if not converging. |
| **Asset Corruption** | Silent failure | Explicit integrity check (FR-001) at startup; fail with clear error. |
| **Singularities** | Simulation crash | Implement "collision reset" logic; log as "reset" event. |
| **Dataset Mismatch** | Cannot run | Verify JSON points to valid assets; if not, block and report missing assets. |

## Decision Rationale

- **Why Single Object?** The CI limit (6h) is insufficient for training on the full GAPartNet dataset with high-fidelity physics. A single object (e.g., a drawer) is sufficient to demonstrate the *mechanism* of PICA and the robustness claim under damping.
- **Why CPU-Only?** The target environment (GitHub Actions free tier) lacks GPU. The plan explicitly avoids GPU-specific libraries to ensure portability.
- **Why Reduced Steps?** To fit the 6-hour window. The goal is *reproduction of the pipeline and claim*, not achieving the exact SOTA performance numbers of the original paper (which may have used 100x more compute).
- **Why Domain Randomization?** To ensure the agent learns to handle variation (the core claim of PICA) rather than overfitting to a single damping setting.