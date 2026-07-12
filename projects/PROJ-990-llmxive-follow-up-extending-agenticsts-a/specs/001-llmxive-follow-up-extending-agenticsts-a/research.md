# Research: llmXive follow-up: extending "AgenticSTS: A Bounded-Memory Testbed for Long-Horizon LLM Agents"

## Executive Summary

This research extends the AgenticSTS testbed by introducing a **Dynamic Memory Policy** that adapts memory retrieval based on real-time game-state entropy. The core hypothesis is that adaptive retrieval can reduce token usage by ≥30% without compromising win rates compared to a static "all-layers" baseline.

The methodology involves:
1.  Performing a **full ablation study** on the training set to generate ground-truth layer utility labels.
2.  Validating the proxy assumption (static logs vs. ablation) on a hold-out set.
3.  Training a lightweight classifier on the **ablation-derived** labels (or validated proxy).
4.  Re-simulating trajectories from initial states for Dynamic, Static, and Random conditions.
5.  Performing rigorous statistical analysis (accounting for potential trajectory divergence).

## Verified Datasets & Engine Sources

**CRITICAL**: The following sources MUST be populated with verified URLs from the project's `Verified datasets` block before execution.

### Primary Dataset: AgenticSTS Trajectories
-   **Source**: AgenticSTS Repository (Release/Commit TBD).
-   **URL**: `[VERIFIED_URL_REQUIRED]` (Must be a specific release or branch containing the 298 trajectory logs).
-   **Verification**: These trajectories are the "Single Source of Truth" (Constitution Principle IV). They must contain per-turn game metrics and final outcomes.
-   **Format**: JSON or CSV logs containing:
    -   `trajectory_id`
    -   `turn_number`
    -   `game_state` (health_ratio, enemy_threat_level, deck_size)
    -   `legal_moves` (for entropy calculation)
    -   `retrieved_layers` (static logs)
    -   `outcome` (win/loss)
-   **Usage**:
    1.  **Ablation**: Re-run the game engine with layers removed to generate ground-truth utility.
    2.  **Training**: Extract features and ground-truth utility to train the classifier.
    3.  **Testing**: Simulate the dynamic policy on a held-out test split.

### Game Engine Source
-   **Source**: AgenticSTS Game Engine.
-   **URL**: `[VERIFIED_URL_REQUIRED]` (Must be the specific version of the engine used to generate the original trajectories).
-   **Requirement**: The engine must be runnable from the `code/` directory to perform re-simulation and ablation studies.

## Proxy Validation Strategy (FR-006)

-   **Goal**: Validate that "information utility" inferred from static logs correlates with ablation-derived ground truth.
-   **Method**:
    1.  Select a **stratified** hold-out set of 20 trajectories (representing the distribution of the full set).
    2.  For each trajectory, compute "static-log utility" (frequency/importance in logs).
    3.  Perform an **ablation study** (remove layer, re-run engine) to get "ground-truth utility".
    4.  Calculate Pearson correlation coefficient ($r$).
    5.  **Success Criterion**: $r \ge 0.7$. If $r < 0.7$, the proxy is invalid.
-   **Gate**: If the proxy is invalid, the classifier training **HALTS**. The system falls back to a heuristic (fixed k=2) or reports the proxy failure in the paper. The training set labels MUST be ablation-derived if the proxy fails.

## Technical Methodology

### 0. Preliminary Feature Validation
-   **Test**: Before training, compute the correlation between `move_entropy` (and other features) and the ablation-derived utility on the training set.
-   **Threshold**: If correlation < 0.3, the entropy assumption is weak. The plan will flag this and consider alternative features or a simpler heuristic.

### 1. Full Ablation Pre-processing (Ground Truth Generation)
-   **Input**: 298 trajectories (or a representative sample if 298 is too slow, but 298 is the target).
-   **Action**: For each trajectory and each memory layer, re-run the game engine with that layer removed from the context.
-   **Output**: A label `layer_utility_ablation` for each layer in each trajectory (measured impact on win rate).
-   **Constraint**: This step is computationally expensive but necessary to avoid circularity. If a full layer traversal is too slow, a stratified sample of trajectories is used, but the sample size must be justified.

### 2. Feature Extraction & Entropy Calculation
-   **Input**: Raw trajectory logs.
-   **Features**:
    -   `health_ratio`: Current health / Max health.
    -   `enemy_threat_level`: Aggregated threat score from enemies.
    -   `deck_size`: Number of cards remaining.
    -   `move_entropy`: Shannon entropy of the probability distribution of legal moves.
-   **Edge Case Handling**:
    -   If entropy calculation returns `NaN` or `Infinity`, default to retrieving **all layers** for that turn and log a warning.

### 3. Classifier Training (FR-002)
-   **Model**: Lightweight Decision Tree or Logistic Regression (CPU-tractable).
-   **Target**: `layer_utility_ablation` (Ground Truth) OR `layer_utility_proxy` (if Proxy Validation passed with $r \ge 0.7$).
- **Training Split**: [deferred] training, [deferred] validation.
-   **Constraint**: If $n < 300$ (current $n=298$), log a warning about marginal statistical power. Default to a fixed $k=2$ heuristic if cross-validation accuracy is below threshold.

### 4. Dynamic Retrieval Agent (FR-003)
-   **Logic**:
    1.  Calculate current turn entropy.
    2.  Query classifier for predicted utility of available layers.
    3.  Select top-$k$ layers until token budget is reached.
    4.  **Token Floor**: If predicted tokens < 256, append "Current Objective" layer.
    5.  **Budget Cap**: If predicted tokens > 4096, truncate least useful layers.

### 5. Simulation & Baselines (FR-004)
-   **Conditions**:
    1.  **Dynamic**: Uses the trained classifier and entropy logic.
    2.  **Static**: Retrieves all layers (baseline).
    3.  **Random**: Retrieves random layers (no-store baseline).
-   **Execution**: **Re-run the game engine** from the initial state of each trajectory for all three conditions.
    -   *Determinism Check*: If the engine is deterministic, trajectories will be identical except for memory content. If non-deterministic, trajectories will diverge.
-   **Metrics**:
    -   `win_rate`: Binary outcome (1/0).
    -   `token_usage`: Total prompt tokens per trajectory.

### 6. Statistical Analysis (FR-005)
-   **Divergence Check**:
    -   If trajectories are **identical** (deterministic engine): Use **McNemar's Test** for paired binary outcomes.
    -   If trajectories **diverge** (non-deterministic engine): Use a **Permutation Test** or **Two-Proportion Z-Test** on aggregate win rates (comparing the distribution of outcomes from the same initial states).
-   **Token Usage Comparison**:
    -   Test: **Paired t-test** (if deterministic) or **Wilcoxon signed-rank** (if non-normal/divergent).
    -   Correction: **Bonferroni**.
-   **Power Analysis**:
    -   Calculate expected discordant pairs for McNemar. If < 10, switch to Permutation Test.
-   **Success Criteria (SC-002)**: Token reduction ≥ 30% with $p < 0.05$ (Bonferroni corrected).
-   **Success Criteria (SC-001)**: Win rate difference $p > 0.05$ (no significant drop).

## Compute Feasibility

-   **Hardware**: GitHub Actions free-tier (CPU, moderate RAM).
-   **Feasibility Check**:
    -   **Dataset Size**: 298 trajectories is small; fits easily in RAM.
    -   **Model Complexity**: Decision Tree/Logistic Regression are CPU-tractable and fast.
    -   **Simulation**: Re-running multiple trajectories across three conditions. Assuming each run takes < 1 minute (simulated or lightweight engine), total time < 15 hours. *Optimization*: If simulation is slow, run on a representative subset (e.g., 100 trajectories) or parallelize if allowed. *Note*: The spec implies re-simulation; we assume the game engine is lightweight enough for CPU-only CI.
    -   **No GPU Required**: All methods (sklearn, statsmodels) run on CPU.

## Decision Rationale

-   **Why Full Ablation?**
    -   **Constraint**: Avoid circularity.
    -   **Rationale**: Training on static logs creates a tautology. Ground truth must be derived from re-simulation.
-   **Why Permutation Test?**
    -   **Constraint**: Trajectory divergence in non-deterministic environments.
    -   **Rationale**: McNemar's test requires paired outcomes on the same path. Permutation tests compare distributions, which is valid for diverging paths.
-   **Why Proxy Validation Gate?**
    -   **Constraint**: Scientific validity.
    -   **Rationale**: Ensures the proxy is not used if it fails, preventing spurious model training.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Proxy Invalid (r < 0.7)** | Dynamic policy trained on wrong signal. | Abort dynamic training; fall back to heuristic (fixed k=2) and report proxy failure in paper. |
| **Simulation Time > 6h** | CI job timeout. | Optimize game engine; run on subset; or parallelize runs. |
| **Entropy NaN/Inf** | Agent crash or starvation. | Implement hard fallback to "all layers" and logging. |
| **Sample Size < 300** | Low statistical power. | Log warning; use non-parametric tests if normality fails; recommend larger dataset in future work. |
| **Trajectory Divergence** | Invalid McNemar test. | Detect divergence; switch to Permutation Test. |
