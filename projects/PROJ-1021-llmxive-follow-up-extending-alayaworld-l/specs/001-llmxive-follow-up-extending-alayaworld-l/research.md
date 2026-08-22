# Research: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

## 1. Problem Statement

The core research question is: *How does the integration of a lightweight, CPU-tractable symbolic logic layer influence the long-horizon semantic consistency of interactive video world models compared to autoregressive generation alone?*

Current autoregressive video models (like AlayaWorld) suffer from "semantic drift" over long horizons (e.g., 60 seconds), where object states (existence, health, inventory) diverge from the logical intent of user actions. This project proposes a **hybrid symbolic-visual architecture** to correct this drift in real-time.

**Scope Boundary & Proxy Limitation**:
Since the AlayaWorld model weights and dataset are not publicly available for programmatic CI execution, this project validates the *correction mechanism* using a **Stochastic Generative Mock (SGM)**. The SGM is a CPU-tractable simulator that mimics the *behavioral failure modes* of a video model (hallucinations, drift, prompt sensitivity) rather than pixel-perfect generation. The results are **Proxy-Validated**: they demonstrate the efficacy of the symbolic logic in a stochastic environment that responds to correction tokens, but they do not measure the drift of the actual AlayaWorld model. This is a necessary constraint for CI feasibility.

## 2. Dataset Strategy

### 2.1 Verified Datasets
- **AlayaWorld**: **NO verified source found.**
  - *Status*: The dataset is not available via a public, programmatic URL (HuggingFace, OpenML, etc.).
  - *Implication*: The project cannot fetch raw AlayaWorld video data on a CI runner.
  - *Mitigation Strategy*: The project utilizes a **Stochastic Generative Mock (SGM)** that generates:
    1. **Action Sequences**: Discrete lists of game-like commands (e.g., "summon", "hit", "die").
    2. **Ground Truth Symbolic Logs**: The deterministic output of the symbolic engine for these actions.
    3. **Stochastic Visual Frames**: A probabilistic visual proxy that simulates the *structure* of AlayaWorld outputs (e.g., object bounding boxes with noise) and, crucially, **responds to correction tokens** by adjusting its hallucination probability.

### 2.2 Data Acquisition Plan
1. **Step 1**: Generate `data/raw/action_sequences.json` (multiple sequences, 10 seeds). Each sequence includes a deterministic `stochastic_seed` derived from `global_seed + sequence_index`.
2. **Step 2**: Run `symbolic_engine.py` to produce `data/processed/symbolic_logs.json` (Ground Truth).
3. **Step 3**: Run `cv_pipeline.py` in "SGM Mode" to generate `data/processed/visual_logs.json`. The SGM uses the `stochastic_seed` to ensure the *same* underlying noise is present in both Baseline and Hybrid runs, differing only by the prompt input.
4. **Step 4**: Create `data/annotated/gt_subset_50.json` manually (or via script) containing ≥50 frames with known object states for FR-007 validation.

## 3. Methodology

### 3.1 Baseline Semantic Drift Quantification (US-1)
- **Input**: Action Sequence.
- **Process**:
  1. Run `symbolic_engine.py` to get logical state trajectory $S_{logic}$.
  2. Run `sgm_generator.py` (Baseline Mode) to get visual state trajectory $S_{visual}$. The SGM samples visual states based on $S_{logic}$ plus stochastic noise, *without* correction tokens.
  3. **Calibrated Drift Score Calculation**:
     - The raw mismatch count $M_{raw}$ is calculated between $S_{logic}$ and $S_{visual}$.
     - The CV pipeline's error rates (False Positive/Negative per object state) are estimated from `data/annotated/gt_subset_50.json`.
     - The **Calibrated Drift Score** is computed as a weighted sum of mismatches: $D_{cal} = \sum_{i} w_i \cdot \mathbb{I}(mismatch_i)$, where $w_i$ is the inverse of the CV confidence for that specific state type. This avoids the invalid additive bias assumption.
- **Output**: Scalar drift score per sequence.

### 3.2 Hybrid Correction Mechanism (US-2)
- **Mechanism**:
  - A `HybridController` monitors $S_{logic}$ and $S_{visual}$ at each timestep.
  - If $\text{StateMismatch}(S_{logic}, S_{visual}) > \text{threshold}$:
    - Generate a "correction token" (textual prompt update, e.g., "Object X is dead").
    - **Feedback Loop**: The SGM receives this token and updates its internal "intent" distribution. The visual state for the *next* frame is re-sampled based on this updated distribution.
    - **Causal Link**: The SGM is designed such that a correction token significantly reduces the probability of maintaining the previous hallucination. This ensures the "Hybrid" run produces different results than the "Baseline" run.
  - **Edge Cases**:
    - *Teleportation*: Log `RENDER_FAILURE` if logical state implies discontinuous movement.
    - *Occlusion*: If CV fails to detect object, assume state persists (low-confidence flag).
    - *Phantom Objects*: If CV detects object not in $S_{logic}$, increment drift score.
- **Limitation**: This validates the *logic's ability to correct a stochastic proxy*, not the real video model's behavior.

### 3.3 Resource Constraint Verification (US-3)
- **Environment**: 2-core CPU, 7GB RAM.
- **Metrics**: Log `peak_ram_gb` and `wall_clock_time_sec` for every sequence.
- **Thresholds**: Time ≤ 1800s (30 min), RAM ≤ 7.0 GB.

### 3.4 Statistical Validation (FR-006, FR-007)
- **Ground Truth Validation (FR-007)**:
  - Run CV pipeline on `data/annotated/gt_subset_50.json`.
  - Calculate detection accuracy. If average accuracy < 85%, the *experiment* is flagged as "inconclusive" (`validation_status: low`), but individual sequence scores are retained with reduced weights.
- **Hypothesis Test (FR-006)**:
  - **RNG Strategy**: Both Baseline and Hybrid runs for a given sequence use the *same* `stochastic_seed` (derived from `global_seed + sequence_index`). This ensures the paired t-test compares the exact same underlying stochastic event under two conditions (with/without correction).
  - Perform paired t-test on **Calibrated Drift Scores** (weighted by CV confidence).
  - $H_0$: $\mu_{baseline} = \mu_{hybrid}$ vs $H_1$: $\mu_{hybrid} < \mu_{baseline}$.
  - Significance level: $\alpha = 0.05$.
  - Input files: `data/results/baseline_scores.json`, `data/results/hybrid_scores.json`.
  - Output file: `data/results/stats_comparison.json`.

## 4. Compute Feasibility & GPU Strategy

- **CPU-First**: The entire pipeline (Symbolic Engine, SGM, CV Primitives, Statistical Tests) is designed for CPU.
  - **Symbolic Engine**: Pure Python, negligible CPU load.
  - **SGM**: A lightweight stochastic process (no heavy neural nets).
  - **CV Pipeline**: OpenCV (template matching/optical flow) is optimized for CPU.
- **GPU Escape Hatch**: Not required. The SGM is a behavioral proxy, not a real video model.
- **Decision**: All methods run on CPU. No GPU offload needed.

## 5. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **AlayaWorld Dataset Unavailable** | Cannot run real visual generation. | Use SGM as a behavioral proxy. Clearly label results as "Proxy-Validated". |
| **CV Accuracy < 85%** | Invalidates drift scores. | Use confidence-weighted aggregation instead of binary discard. Flag experiment as "inconclusive" if average accuracy is low. |
| **Memory Overflow (>7GB)** | CI failure. | Stream data; process one sequence at a time. |
| **Non-Deterministic Symbolic Engine** | Invalidates ground truth. | Enforce pure Python, no random seeds in symbolic logic. |

## 6. Conclusion

The proposed methodology rigorously tests the hypothesis that symbolic grounding reduces semantic drift *in a stochastic environment that mimics video model failure modes*. By strictly adhering to CPU constraints, implementing a robust Ground Truth Validation step, and using a paired t-test with shared noise streams, the project ensures reproducibility and statistical validity for the proxy. The results are explicitly framed as "Proxy-Validated" to acknowledge the limitation of not testing the real AlayaWorld model.