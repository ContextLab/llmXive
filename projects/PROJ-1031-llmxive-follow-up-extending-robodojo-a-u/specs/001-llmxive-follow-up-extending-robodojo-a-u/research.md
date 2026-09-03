# Research: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

## 1. Research Question & Hypothesis

**Primary Question**: To what extent is high-fidelity continuous physics simulation necessary for successful long-horizon robot manipulation planning, and can topological symbolic abstractions alone suffice to bridge the sim-to-real gap in generalist policies?

**Null Hypothesis ($H_0$)**: There is no statistically significant difference in task completion success rates between the high-fidelity RoboDojo Neural Policy baseline and the proposed CPU-tractable Symbolic-Dojo approach (Wilcoxon signed-rank test, $\alpha = 0.05$).

**Alternative Hypothesis ($H_1$)**: The Symbolic-Dojo approach results in a statistically significant reduction in success rate (indicating physics fidelity is necessary) OR a significant reduction in compute overhead with no significant reduction in success rate (indicating symbolic abstractions suffice).

## 2. Dataset Strategy

The project relies on the **RoboDojo Benchmark** dataset, which provides both simulation task specifications and real-world execution videos.

| Dataset Component | Source URL (Verified) | Usage | Access Method |
|:--- |:--- |:--- |:--- |
| **Simulation Tasks** | ` | Source of task definitions for the Oracle control and initial state generation. | `datasets.load_dataset(..., streaming=True)` |
| **Real-World Tasks** | ` | Ground truth for real-world execution validation (US-2). Contains **raw video frames**. | `datasets.load_dataset(..., streaming=True)` |
| **Task Metadata** | ` | Mapping of task IDs to success criteria and affordance graphs. | `hf_hub_download` |

**Dataset Version**: `RoboDojo-Benchmark/RoboDojo` (Commit: `v3.0.1`). This version is verified to contain the specific task subset required for this study.

**Data Availability Assessment**:
- **Open Source**: Both datasets are publicly available on Hugging Face without authentication or data-use agreements.
- **Feasibility**: The parquet files are streamed directly. The total size of the specific tasks is well within the available disk and RAM limits when processed in chunks.
- **Variable Fit**: The dataset contains **raw visual observations (video frames)** and ground-truth task labels. The plan explicitly extracts visual features via `vision_encoder.py` to generate `SemanticEmbedding` (FR-001) and uses the metadata to define `SymbolicState` predicates (FR-002). No continuous physics variables (friction coefficients, mass) are required from the dataset for the symbolic layer, aligning with the "Simulation Fidelity Independence" principle.
- **Task Selection**: A `task_selection.py` script filters the dataset for the specific 18 task IDs before processing to ensure consistency.

**Handling Missing Data**:
- If a specific task ID is missing from the real-world subset, the system will skip that task and log a "Data Gap" warning. The statistical analysis will proceed with $N < 18$, adjusting the power analysis accordingly.

## 3. Methodology

### 3.1. Symbolic Abstraction Layer (CPU-Tractable)
1. **Vision Encoding**: Input video frames (raw) are passed through a frozen **MobileViT** encoder (CPU-optimized) to generate high-dimensional semantic embeddings. This strips continuous dynamics.
2. **State Mapping**: Embeddings are mapped to a discrete `SymbolicState` graph using a **deterministic thresholding** function (e.g., `pred > 0.6` implies `graspable`).
 - **Conflict Resolution**: If multiple predicates are active, the system prioritizes "safety" predicates (e.g., `blocked` overrides `graspable`).
 - **Ambiguity Logging**: If a predicate score is between 0.4 and 0.6, the system logs an "Ambiguity Warning" but proceeds with the most likely state.
 - **Calibration**: Thresholds are set using a validation set (a subset of tasks) in Phase 0.5.
3. **Planning**: A **A* (A-Star)** planner operates on the discrete graph.
 - *Search Space*: Nodes = `SymbolicState`, Edges = Discrete Actions.
 - *Heuristic*: Admissible heuristic based on graph distance to goal state.
 - *Constraint*: Must complete within 60s on 2-core CPU.

### 3.2. Execution & Validation
1. **Sim-to-Real Adapter (FR-009)**:
 - **Protocol**: "Frozen Feature + Linear Probe". The MobileViT backbone is frozen; a linear layer is trained on the 14-task subset to map embeddings to control parameters.
 - **Validation**: A subset of hold-out tasks is used to verify generalization before final training on all 18.
2. **Real-World Execution**: The generated `ActionSequence` is executed by the **Adapted Low-Level Controller**.
 - *Failure Logging*: If execution fails, the system logs the step index and classifies the failure as "Planner Infeasibility" (wrong plan) or "Controller Execution Failure" (plan correct, execution failed).
3. **Oracle Control (Diagnostic Only)**:
 - **Definition**: A "Perfect Low-Level Executor" (simulated ground-truth in a high-fidelity physics engine).
 - **Purpose**: To measure the theoretical maximum success rate of the symbolic planner *if* the controller were perfect.
 - **Limitation**: The Oracle success rate is expected to be near-perfect. The "Physics Fidelity Gap" ($1 - Success_{RealWorld}$) is a diagnostic of the *controller's* domain shift failure, not a validation of the planner's physics necessity. The primary hypothesis test (SC-001) relies **only** on Real-World execution.

### 3.3. Statistical Analysis
1. **Comparison**: Paired success rates (Symbolic vs. Baseline) across multiple tasks.
2. **Test**: **Wilcoxon signed-rank test** (non-parametric, suitable for small $N=18$ and non-normal distributions).
 - $H_0$: Median difference = 0.
 - Significance level: $\alpha = 0.05$.
 - **Effect Size**: Rank-biserial correlation will be reported alongside p-values to account for low power.
3. **Compute Metrics**: Percentage reduction in CPU cycles and wall-clock time compared to the GPU baseline.
4. **Catastrophic Failure Rate**: Calculate the percentage of tasks failing due to "Hardware Error" or "Timeout". Compare to the 5% threshold (SC-005).
5. **Physics Fidelity Gap**: $Gap = Success_{Oracle} - Success_{RealWorld}$. (Diagnostic only).

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: Only one primary hypothesis test (Wilcoxon) is performed on the main metric (success rate). No family-wise error correction is needed as the test is singular.
- **Power Analysis**: With $N=18$ paired samples, the power to detect a large effect size ($d_z \approx 0.8$) at $\alpha=0.05$ is approximately 0.75. The study is **underpowered** to detect small effects. This limitation is explicitly acknowledged in the final report. Effect sizes will be reported to provide context.
- **Causal Inference**: This is an observational comparison of two methods on the same tasks. No randomization of tasks is performed (all tasks are used). Claims are framed as "comparative performance" rather than causal effects of the method on the robot's physical properties.
- **Collinearity**: The `SymbolicState` predicates are defined as topological relationships. Collinearity between predicates (e.g., `graspable` and `placeable`) is acknowledged but handled descriptively; the planner treats them as distinct logical nodes.
- **Measurement Validity**: MobileViT is a standard, validated architecture for mobile/efficient vision. The RoboDojo benchmark provides validated task definitions and success criteria.

## 5. Decision Rationale

| Decision | Rationale |
|:--- |:--- |
| **CPU-First Planning** | The core hypothesis is about reducing computational barriers. A GPU-based planner would invalidate the "CPU-tractable" claim. |
| **Streaming Data** | The full RoboDojo dataset may exceed RAM. Streaming ensures the full dataset is used without OOM errors, adhering to the "Data Hygiene" and "Compute Feasibility" constraints. |
| **Oracle Control** | Essential to isolate the "Physics Fidelity Gap" as a controller diagnostic. Without it, a failure in real-world execution could be misattributed to the planner rather than the controller. |
| **Wilcoxon Test** | With $N=18$, normality assumptions for a t-test are weak. Wilcoxon is robust for small sample sizes and ordinal/binary success data. |
| **Split-Data Adaptation** | Prevents the confound of overfitting the controller to the test set, ensuring the success rate reflects the planner's logic, not the controller's memorization. |