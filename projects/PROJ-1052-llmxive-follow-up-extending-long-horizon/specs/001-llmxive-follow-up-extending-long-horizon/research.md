# Research: llmXive Follow-up: Reward Fidelity vs. Error Recovery Density

## Research Question
What is the non-linear threshold (inflection point) where reducing **reward signal fidelity** (coarsening dense rewards to binary/ternary) causes a statistically significant decline in an LLM agent's ability to recover from errors due to the loss of **recovery-critical context segments**?

## Dataset Strategy

The study relies on the **AgentBench** dataset (specifically the `os` and `web` sub-tasks which are long-horizon).

| Dataset Name | Source Type | Verified URL / Loader | Justification |
| :--- | :--- | :--- | :--- |
| **AgentBench** | HuggingFace Dataset | `datasets.load_dataset("THUDM/agentbench")` (Verified) | A verified, public dataset containing long-horizon tasks with environment snapshots and success flags. It provides the necessary trajectory data to define "stagnant" segments and "error recovery" events. |

**Data Availability & Feasibility**:
- **Access**: The dataset is open and directly downloadable via the HuggingFace `datasets` library. No credentials or data-use agreements are required.
- **Streaming**: To respect the 7 GB RAM limit, the implementation will use `streaming=True` for initial inspection. For the full execution run, the dataset will be loaded in chunks or sampled if the full size exceeds memory, with the sampling strategy logged.
- **Variable Fit**: The dataset contains `observation` (environment snapshot), `action`, and `success` fields. The "recovery-critical" segments will be derived programmatically from the `observation` snapshots (state-diff metric), satisfying FR-007. If native reward signals are missing, a **progress proxy** (e.g., number of unique files touched) will be used to simulate reward signals.

**Note**: If the dataset lacks specific variables required to define "stagnant" vs. "critical" segments, the system will fail gracefully with `ERR_MISSING_VAR` as per the spec's edge case handling.

## Methodology

### Phase 1: Baseline Execution & Ground Truth (FR-001, FR-002)
1.  **Download**: Fetch `THUDM/agentbench` (subset of `os`/`web` tasks, a representative sample).
2.  **Agent Setup**: Initialize `Qwen-1.5-1.8B` (or `Llama-3-8B-int4` via `llama-cpp-python`) in CPU mode.
3.  **Execution**: Run all tasks with **Full Context** and **Dense Rewards** (or progress proxy).
4.  **Logging**:
    - Record `success` (binary).
    - **Natural Recovery**: Identify tasks where the agent *naturally* recovers from a failure state (e.g., a failed command followed by a successful one) without synthetic injection.
    - Identify **Recovery Segments**: For each successful recovery, calculate the **semantic state-diff** between the pre-error and post-recovery environment snapshots. A segment is "critical" if its removal (simulated ablation) causes the reference model to fail, or if the state-diff magnitude is high. Tag segments where the contribution > 5% (FR-007).
    - Store `recovery_segment_ids` for each task.

### Phase 2: Fidelity Manipulation & Pruning (FR-003, FR-004, FR-009)
1.  **Fidelity Levels**: Define 2 conditions:
    - `Binary`: Coarsen rewards to "progress" (>0) vs "stagnant" (0).
    - `Dense Pruning` (Control): Use the *dense* reward signal to drive pruning (High-Fidelity Pruning).
2.  **Pruning Logic**:
    - For `Binary`: Prune context segments tagged as "stagnant" by the binary signal.
    - For `Dense Pruning`: Prune segments tagged as "stagnant" by the dense signal.
3.  **Execution**: Re-run all tasks under each condition.
4.  **Logging**:
    - Record `success` (binary).
    - Log `tokens_consumed`.
    - Verify if `recovery_segment_ids` from Baseline were retained or pruned.

### Phase 3: Statistical Analysis (FR-005, FR-006, FR-008)
1.  **Model**: Perform a **Cochran-Armitage Trend Test** (or Fisher's Exact Test for pairwise comparisons) to model the relationship between `Fidelity` (ordinal) and `Success` (binary).
    - *Note*: Logistic Regression is rejected due to N=46 and low EPV.
2.  **Inflection Point**: Calculate the point of **maximum curvature** in the empirical success rate curve across fidelity levels.
3.  **Correction**: Apply **Benjamini-Hochberg** correction if multiple pairwise comparisons are performed.
4.  **Fallback**: If the trend test is inconclusive, report the descriptive success rates and confidence intervals.

## Compute Feasibility & Escape Hatch

- **CPU Only**: The plan uses `llama-cpp-python` with low-bit quantization on a 2-core CPU runner.
- **Model Selection**:
    - Primary: `Llama-3-8B` (int4).
    - Fallback: `Qwen-1.5-1.8B` (int4) if 8B exceeds 7 GB RAM.
- **No GPU Offload**: The experiment is designed to run entirely on CPU to ensure reproducibility on a fresh GitHub Actions runner. No external GPU environments are used.

## Statistical Rigor

- **Multiple Comparisons**: Benjamini-Hochberg correction applied to pairwise comparisons (if any).
- **Sample Size**: N=46 tasks. The plan explicitly uses **Cochran-Armitage** (robust for small N) rather than Logistic Regression to avoid EPV violations.
- **Causal Claims**: The study is experimental regarding the *pruning intervention*. Claims will be framed as "associational between fidelity and recovery" with the caveat of the small sample size.
- **Collinearity**: The analysis explicitly measures the overlap between "stagnant" (pruned) and "critical" (recovery) segments to validate the mechanism.

## Limitations

- **Task Count**: A limited number of tasks may be underpowered for complex statistical modeling.
- **Model Size**: Qwen-1.5-1.8B may not capture the full complexity of "long-horizon" reasoning compared to larger models, but it is the only option fitting the free-tier constraints.
- **Heuristic Validity**: The "state-diff" heuristic for identifying recovery segments is an approximation.
- **Dataset**: AgentBench is used as a proxy for "Long-Horizon-Terminal-Bench" due to the latter's non-existence.