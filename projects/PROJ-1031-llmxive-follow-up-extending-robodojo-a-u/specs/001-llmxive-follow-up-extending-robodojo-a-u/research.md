# Research: llmXive Follow-up: Extending RoboDojo with Symbolic Abstractions

## Research Question
To what extent is high-fidelity continuous physics simulation necessary for successful long-horizon robot manipulation planning, and can topological symbolic abstractions alone suffice to bridge the sim-to-real gap in generalist policies?

## Dataset Strategy

| Dataset Name | Source URL (Verified) | Usage | Accessibility |
| :--- | :--- | :--- | :--- |
| **RoboDojo (LERobot v3.0)** | `https://huggingface.co/datasets/OpenMOSS-Team/robodojo-lerobot-v3.0/resolve/main/data/chunk-000/file-000.parquet` | Primary source for task specifications, visual observations, and ground-truth trajectories. | **Open** (Direct download via `datasets` library). |
| **RoboDojo (Benchmark)** | `https://huggingface.co/datasets/RoboDojo-Benchmark/RoboDojo/resolve/main/data/RoboDojo_ee_lerobot_v30_video/data/chunk-000/file-000.parquet` | Secondary verification of task definitions and video frames. | **Open** (Direct download). |
| **RoboDojo Assets (BUILD_COMPLETE)** | `https://huggingface.co/datasets/didfd/robodojo-assets-packed/resolve/main/BUILD_COMPLETE.json` | Task metadata and success criteria definitions. | **Open** (Direct download). |

**Strategy**:
1.  **Streaming**: Use `datasets.load_dataset(..., streaming=True)` to avoid loading the full dataset into RAM on the GitHub Actions runner.
2.  **Sampling**: For the initial feasibility test, sample a representative subset of tasks (as per spec) to ensure the pipeline runs within the CI time limit.
3.  **No Gated Data**: The plan strictly avoids ADNI, HCP, or other gated datasets. The RoboDojo dataset is fully open and verified.

## Methodology

### 1. Semantic Embedding Generation (FR-001, FR-002)
- **Model**: Frozen MobileViT (CPU-optimized).
- **Process**: Extract frames from RoboDojo video streams. Pass through MobileViT to generate high-level vectors.
- **Constraint**: No fine-tuning of the vision encoder; only frozen inference to ensure CPU tractability.
- **Mapping Validation**: A critical step is added to validate the accuracy of the mapping from continuous embeddings to discrete `SymbolicState` predicates. If the mapping is noisy, the "Planner Infeasibility" metric is confounded by "Encoder Ambiguity". We will report the mapping accuracy as a separate metric.
- **Output**: `SemanticEmbedding` vector (stripped of continuous physics dynamics).

### 2. Symbolic State Mapping (FR-002, FR-003)
- **Graph Construction**: Map embeddings to `SymbolicState` nodes representing object affordances (e.g., `Graspable`, `Stable`, `Connected`).
- **Abstraction**: Explicitly exclude continuous variables (friction, mass, exact pose) in favor of topological relations.
- **Validation**: Validate against `SymbolicState` schema (Contract T005a).

### 3. Symbolic Planning (FR-003, US-1)
- **Algorithm**: A* Search or MCTS (Monte Carlo Tree Search).
- **Goal**: Generate a sequence of discrete sub-goals (ActionSequence) from Start State to Goal State.
- **Constraint**: Must execute on CPU within 60s per task.
- **Fallback**: If A* fails (state space too large), switch to MCTS with a fixed depth limit.

### 4. Execution & Failure Detection (FR-004, FR-006, T024)
- **Oracle Executor (FR-010, US-4)**: A **deterministic, non-physics rule-based verifier**. It checks if the generated symbolic sequence matches the ground-truth task graph topology. It does *not* simulate physics.
    - **Logic**: The Oracle is a static "Ground-Truth Graph Matcher". It validates if a proposed sequence is a valid path in the known task graph.
    - **If Oracle Rejects**: The planner failed to find a valid topological path. This is labeled **"Planner Infeasibility"**. (Note: A perfect matcher on a valid task graph should not reject a valid path; rejection implies the planner's output was invalid).
    - **If Oracle Accepts**: The plan is logically valid (topologically feasible).
- **Real-World Executor (FR-004, US-2)**: Uses adapted RoboDojo weights to execute the plan in the real environment.
    - **If Oracle Accepts but Real-World Fails**: The low-level controller could not bridge the gap. This is labeled **"Controller Execution Failure"**.
- **Failure Logic**: Explicitly distinguishes between Planner Infeasibility and Controller Execution Failure.
- **Logging**: Write to `data/interim/execution_logs.parquet` with columns: `task_id`, `step`, `outcome`, `failure_mode`.

### 5. Statistical Analysis (FR-005, US-3)
- **Test**: Wilcoxon signed-rank test (non-parametric, paired).
- **Hypothesis**: $H_0$: Median difference in success rates (Symbolic vs. Baseline) = 0.
- **Significance**: $\alpha = 0.05$ (Source: Replication crisis, https://en.wikipedia.org/wiki/Replication_crisis).
- **Metrics**:
    - Success Rate (Symbolic vs. Baseline).
    - Compute Overhead Reduction (%).
    - Physics Fidelity Gap (Oracle Success - Real Success).
    - **Catastrophic Failure Rate**: % of tasks with complete abandonment (SC-005).
- **Control for Confounds**:
    - **Neural Policy Abstraction Proxy**: To isolate the "planning" variable from the "execution" variable, the study will run the Neural Policy in the RoboDojo simulation environment. The resulting continuous trajectories will be segmented and clustered to extract a discrete sequence of sub-goals (a "high-level trace"). This trace is then validated against the Oracle. This creates a **(Neural+Oracle)** control group, allowing for a fair comparison of the *planning* capability of the Symbolic vs. Neural approaches, independent of the execution fidelity.
    - The final comparison is between (Symbolic+Real) and (Neural+Real), with the (Neural+Oracle) and (Symbolic+Oracle) groups providing the isolation of the planning variable.

## Power Analysis & Sample Size Justification

- **Sample Size**: N=18 tasks.
- **Limitation**: With N=18, the Wilcoxon signed-rank test has low statistical power to detect small effect sizes.
- **Mitigation**: The study is explicitly framed as exploratory for N=18. We will report effect sizes (e.g., rank-biserial correlation) alongside p-values. A power analysis will be conducted to determine the minimum detectable effect size at $\alpha=0.05$ and power=0.80. If the effect size is too small to be detected with N=18, this limitation will be highlighted in the final report.
- **Minimum Detectable Effect**: For N=18, $\alpha=0.05$, Power=0.80, the minimum detectable effect size (rank-biserial correlation) is approximately 0.55. Effects smaller than this may result in a Type II error (failing to reject a false null hypothesis).

## Compute Feasibility (CPU-First)

- **Vision Encoder**: MobileViT is lightweight and runs on CPU. Quantization (int8) will be applied if memory > 6GB.
- **Planner**: A*/MCTS on a graph of <1000 nodes is trivial for 2 CPU cores.
- **Data**: Streaming Parquet avoids OOM.
- **No GPU Required**: The entire pipeline (planning, encoding, stats) is designed to run on the GitHub Actions free-tier (multi-core CPU, sufficient RAM).
- **Escape Hatch**: None required. If the "Perfect Executor" simulation becomes too heavy, it will be simplified to a deterministic rule-based simulator rather than a full physics engine, as the goal is to isolate the *planner*, not the physics fidelity.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Ambiguous Embeddings** | Planner cannot map to unique state. | Implement a "Manual Review" flag in the logging system; if >5% ambiguous, report as "Encoder Ambiguity" (confound) rather than Planner Infeasibility. |
| **Real-World Failure Rate** | High failure rate obscures planner performance. | Use the Oracle Executor to separate planner failure from controller failure (FR-010). |
| **Compute Time** | >6 hours for 18 tasks. | Parallelize task execution (if runner allows) or reduce task count to a minimal set for initial validation. |
| **Data Access** | HuggingFace rate limits. | Use `datasets` library with caching and retries. |
| **Statistical Power** | N=18 may be insufficient to detect small effects. | Acknowledge limitation in report; focus on effect size estimation rather than strict significance. |

## Decision Rationale

- **Why A*/MCTS?** A* is optimal for small graphs; MCTS is robust for larger, uncertain state spaces. Both are CPU-tractable.
- **Why MobileViT?** It is the smallest viable transformer for visual encoding that can run on CPU without quantization artifacts.
- **Why Wilcoxon?** Success rates are binary (0/1) and non-normally distributed; Wilcoxon is the standard for paired non-parametric data.
- **Why Rule-Based Oracle?** Using a physics-based Oracle would conflate planner validity with physics fidelity. A rule-based graph matcher isolates the *planner's* logical correctness, which is the core hypothesis.
- **Why Explicit Power Analysis?** To avoid Type II errors and ensure the study's limitations are transparently reported.
- **Why Neural Policy Abstraction Proxy?** To isolate the "planning" variable from the "execution" variable, enabling a scientifically sound comparison between Symbolic and Neural planning capabilities.