# Research: 001-tutorial-bias-analysis

## 1. Problem Statement & Hypothesis

**Hypothesis**: Agents trained exclusively on linear GUI trajectories (simulating video-derived data) exhibit a "tutorial bias," performing significantly worse on non-linear tasks (error recovery, modal handling) compared to agents augmented with synthetic error-recovery data (Hybrid), despite similar performance on linear "happy path" tasks.

**Null Hypothesis ($H_0$)**: There is no statistically significant difference in error-recovery success rates between the Linear-Only Proxy agent and the Hybrid agent on the non-linear benchmark subset.

**Revised Hypothesis Scope**: Due to the lack of verified video-derived datasets, the hypothesis is reframed as a comparison of **Linear-Only** vs. **Linear+Error** training distributions using the best available verified proxies. The study tests the *mechanism* of error recovery, acknowledging the modality limitation.

## 2. Dataset Strategy

### 2.1. Benchmark Generation (Synthetic)
Since no verified dataset exists containing 500 labeled non-linear GUI tasks with explicit error states, the benchmark is **synthetically generated** (FR-001).
- **Source**: Rule-based simulator using a lightweight HTML/JS environment (headless browser via `playwright`).
- **Taxonomy Split Strategy**:
  - **Taxonomy Set A (Training)**: Used to generate synthetic error-recovery trajectories for the **Hybrid** agent. Includes errors like "Modal Blocking", "Invalid Input".
  - **Taxonomy Set B (Testing)**: Used to generate the **Benchmark Test Set**. Includes errors like "Network Timeout", "Server Error".
  - **Taxonomy Set C (Generalization)**: A third, disjoint set used for a "Generalization Check" to verify the agent isn't just memorizing A or B.
  - **Independence**: The rule definitions (taxonomy) are disjoint. This ensures the Hybrid agent cannot memorize the test generator's logic.
- **Structure**: 500 tasks (subject to pilot adjustment), 250 linear (control), 250 non-linear (test). Each non-linear task has at least one injected error state from Taxonomy Set B and a defined recovery path.
- **Verification**: The generator script will output a manifest with task IDs, error types, and recovery logic.

### 2.2. Agent Training Data
- **Linear-Only Proxy (WildGUI Proxy)**: Fine-tuned on linear GUI trajectories from verified proxy datasets.
  - **Proxy Strategy**: Since no verified "WildGUI" dataset exists, we use **Uni-GUI-OpenMobile** (linear trajectories) and **Qwen-VL** chat logs (linear instructions).
  - **Construct Validity Note**: These datasets are static (not video-derived). The plan acknowledges this modality mismatch. The hypothesis is tested on the *absence of error data* in the training distribution, not the *video modality* itself.
  - **Why these proxies?**: They are verified sources that explicitly *lack* error recovery examples, making them the ideal proxy for the "Linear-Only" condition.
  - **Verified Sources Used**:
    - `Uni-GUI-OpenMobile`: https://huggingface.co/datasets/UI-MOPD/Uni-GUI-OpenMobile/resolve/main/split1_1004_ExpenseAddMultipleFromGallery/result.json
    - `Qwen-VL` Chat Logs: https://huggingface.co/datasets/open-llm-leaderboard-old/details_JosephusCheung__Qwen-VL-LLaMAfied-7B-Chat/resolve/main/2023-10-10T07-39-47.100914/details_harness|arc:challenge|25_2023-10-10T07-39-47.100914.parquet
- **Baseline (Generic Instruction)**: Fine-tuned on generic instruction-following data (e.g., Alpaca) to serve as a control for "lack of GUI grounding". This isolates the effect of *GUI-specific* linear training from *general* instruction following.
- **Hybrid**: Fine-tuned on linear trajectories (from proxies) + synthetic error-recovery trajectories (from Taxonomy Set A).
 - **Data Ratio**: [deferred] linear trajectories, 20% synthetic error-recovery trajectories.
 - **Data Leakage Prevention**: The 20% synthetic data uses Taxonomy Set A, while the test set uses Taxonomy Set B. The generator logic is randomized to prevent memorization.

### 2.3. Dataset Variable Fit
- **Required**: Task goal, initial state, error state, recovery path.
- **Available**: The synthetic generator provides all required variables. The verified datasets provide linear trajectories.
- **Gap**: No verified dataset provides *explicit* non-linear error recovery labels. This is the **primary justification** for the synthetic benchmark.

## 3. Methodology

### 3.1. Agent Variants
1.  **Baseline**: Fine-tuned on generic instruction data only. Controls for "lack of GUI grounding".
2.  **Linear-Only Proxy**: Fine-tuned on linear GUI trajectories (Uni-GUI/Qwen-VL) only. Controls for "lack of error data" in a GUI context.
3.  **Hybrid**: Fine-tuned on linear trajectories (from proxies) + synthetic error-recovery trajectories (Taxonomy Set A, 80/20 ratio).

### 3.2. Evaluation Protocol
- **Environment**: Headless browser (Chromium) running a simplified HTML GUI.
- **Loop**:
  1. Load task (Goal + Initial State).
  2. Agent observes state, predicts action.
  3. Simulator executes action, updates state.
  4. If error state encountered (from Taxonomy Set B), agent must recover.
  5. Loop until success, failure, or 50 steps (FR-006).
- **Logging**: Full trajectory (state, action, reward) stored in JSON (FR-003).

### 3.3. Statistical Analysis
- **Metric**: Success Rate (Linear vs. Non-Linear).
- **Tests**:
  1.  **Baseline vs. Linear-Only Proxy**: McNemar's test to verify that the two linear-only agents perform similarly (validating the control).
  2.  **Linear-Only Proxy vs. Hybrid**: McNemar's test on paired outcomes for non-linear tasks (Taxonomy Set B). Primary test of "tutorial bias".
  3.  **Baseline vs. Hybrid**: McNemar's test to measure the total effect of adding error data + GUI grounding.
- **Power Analysis**: Post-hoc calculation of power based on observed discordant pairs (FR-007). Target power ≥ 0.8.
- **Sensitivity**: Vary error-injection thresholds by ±10% to test robustness (SC-005).
- **Generalization Check**: Evaluate agents on a small set of "unseen" error types (Taxonomy Set C) to verify generalization beyond the training/test split.

## 4. References & Verified Sources

- **GUI Error Taxonomy**: (To be cited in implementation). *Note: The plan requires a documented taxonomy. A standard reference like "Error Patterns in Human-Computer Interaction" or a specific GUI paper will be cited.*
- **WildGUI/Video2GUI**: No verified source found in the input block. The plan uses a **proxy** from verified sources (`Uni-GUI`, `Qwen-VL`) to approximate the linear training distribution.
- **Verified Datasets**:
  - `Uni-GUI-OpenMobile`: https://huggingface.co/datasets/UI-MOPD/Uni-GUI-OpenMobile/resolve/main/split1_1004_ExpenseAddMultipleFromGallery/result.json
  - `Qwen-VL` Chat Logs: https://huggingface.co/datasets/open-llm-leaderboard-old/details_JosephusCheung__Qwen-VL-LLaMAfied-7B-Chat/resolve/main/2023-10-10T07-39-47.100914/details_harness|arc:challenge|25_2023-10-10T07-39-47.100914.parquet

## 5. Feasibility & Risk Mitigation

- **Compute Risk**: 500 tasks × 3 agents × 50 steps = 75,000 inference steps.
  - **Pilot Study**: Run multiple tasks per agent to measure actual inference latency.
  - **Fallback Strategy**: If latency > 4.8s/step (projected 6h runtime):
    1.  Dynamically reduce sample size (N) to ensure total runtime < 6h while maintaining power ≥ 0.8 (calculated via post-hoc power analysis).
    2.  Or, reduce step limit (e.g., to a lower threshold) if complexity allows.
  - *Timeout*: If runtime > 5 hours, abort and report timeout (Edge Case).
- **Memory Risk**: A defined storage limit.
  - *Mitigation*: Load model once, reuse for all tasks. Clear GPU cache (N/A for CPU) and Python garbage collect between agents.
- **Statistical Risk**: Low discordant pairs may lead to low power.
  - *Mitigation*: If power < 0.8, report the limitation and interpret results as "inconclusive" rather than "no difference".
- **Modality Mismatch**: The proxy datasets are static, not video-derived.
  - *Mitigation*: Explicitly state this limitation in the paper. The hypothesis is tested on the "absence of error data" variable, not the "video modality".
- **Circularity Risk**: Training and testing on the same error types.
  - *Mitigation*: Use disjoint Taxonomy Set A (training) and Taxonomy Set B (testing). Add Taxonomy Set C for generalization check.
- **Validity of Synthetic Benchmark**: Success on synthetic rules does not guarantee real-world robustness.
  - *Mitigation*: Frame the study as a "controlled proof-of-concept" for the *mechanism* of error recovery. The Generalization Check (Taxonomy Set C) tests if the agent learns the *concept* of error recovery.