# Research: llmXive follow-up: extending "Beyond the Current Observation: Evaluating Multimodal Large Language M"

## Research Question

Does reducing the input modality from raw visual frames to deterministic ASCII text representations improve state retention (reduce "Memory Gap") in LLM agents navigating the RNG-Bench 3D Maze environment?

## Hypothesis

**H1**: The "Memory Gap" score for the text-only agent (ASCII input) will be strictly lower than the "Memory Gap" score for the baseline MLLM (visual input) when both are evaluated on the same environment instances.
*   **Rationale**: The hypothesis is that *Visual input* causes memory failure due to high-dimensional token consumption. By isolating the input modality (Text Agent vs. Visual Baseline) while controlling for the environment (same seeds), we test if the Text representation improves retention of hidden history.

**H0**: There is no difference in the distribution of "Memory Gap" scores between the text-only agent and the baseline MLLM.

## Methodology

### 1. Environment & Data Strategy

**Dataset Source**: RNG-Bench 3D Maze Environment.
*   **Access Strategy**: The project will use the open-source RNG-Bench codebase to generate game instances programmatically. No external download of pre-baked images is required; the environment is instantiated in-memory using pinned random seeds.
*   **Variable Fit**: The environment provides:
    *   `grid_state`: 3D array representing walls, floor, player, items.
    *   `item_locations`: Ground truth coordinates for keys, doors, etc.
    *   `event_log`: Sequence of actions and observations.
*   **Feasibility**: Generating these instances in-memory on a CPU runner is computationally trivial and avoids the need for large storage or network downloads.

**Data Generation (FR-001)**:
For each seed, the system will:
1.  Instantiate the 3D Maze.
2.  Convert the `grid_state` to an ASCII string (`#` for walls, `.` for floor, `M` for player).
3.  Append JSON events (`{"t": t, "event": "saw_key"}`) to a log.
4.  Store the ground-truth internal state variables (item locations) separately for scoring.

### 2. Agent Implementation

**Model Selection**: A quantized text-only LLM (e.g., Qwen2-3B-Instruct or Llama-3-8B-Instruct 4-bit).
*   **Rationale**: Fits within 7GB RAM on CPU (Constitution Principle VII).
*   **Inference Engine**: `llama-cpp-python` (CPU backend) or `transformers` with `bitsandbytes` (CPU mode).
*   **Input Format**: Concatenation of:
    *   System Prompt: Instructions for maintaining a "mental map".
    *   Current State: ASCII Grid.
    *   History: JSON Event Log (truncated if necessary).
*   **Output Format**: JSON `{"move": "up", "mental_map": "..."}`.

**Loop Logic (FR-003)**:
1.  Initialize state.
2.  Render ASCII + Log.
3.  Prompt Model -> Get Action + Mental Map.
4.  Execute Action in Environment.
5.  Repeat until goal or step limit (500 steps).

### 3. Baseline Strategy (FR-008 Override)

The baseline MLLM (from the original paper) will be re-run on the **exact same Visual inputs** (raw frames) generated for the same RNG-Bench seeds.
*   **Rationale**: The hypothesis is that *Visual input* causes memory failure. To test this, we must compare the Text Agent (Text Input) against the Baseline (Visual Input) on the *same* ground-truth state.
*   **Baseline Adapter**: Since the baseline outputs visual reasoning or unstructured text, a `baseline_adapter.py` module will parse the baseline's output into a **structured JSON "mental map"** (e.g., `{"items": [{"type": "key", "pos": [x,y,z]}]}`).
*   **Comparison**: Both agents are evaluated against the same "Hidden State" ground truth. The Text Agent receives ASCII; the Baseline receives Visual frames. This isolates the modality variable (Text vs. Visual) while controlling for environment complexity and seed variance.
*   **Note**: We do *not* adapt the baseline to ASCII, as that would invalidate the causal claim by removing the visual modality from the baseline. This approach is a **Deviation from Spec FR-008**, which mandates ASCII inputs for the baseline. A Spec Kickback has been initiated to correct FR-008.

### 4. Metrics & Statistical Analysis

**Memory Gap Metric (FR-004, FR-006 Deviation, FR-007)**:
Calculated at critical decision points (e.g., when approaching a door).
$$ \text{Gap} = \text{StructuredDiff}(\text{AgentMap}, \text{GroundTruth}_{\text{hidden}}) + \sum \text{Penalty}(\text{MissingItems}) $$
*   **StructuredDiff**: The agent's "mental map" (text or parsed from visual output) is converted into a canonical JSON object. This is compared to the ground truth JSON.
    *   **Exact Match**: For discrete items (key location, door state).
    *   **Semantic Similarity**: For descriptive text (e.g., "I remember a key in the north room"), using cosine similarity of sentence embeddings (e.g., `all-MiniLM-L6-v2`).
*   **Hidden State Masking (FR-007)**: Crucially, the ground truth comparison string **excludes** items currently visible in the ASCII frame or Visual input. Only items that are *not* in the current view (hidden history) are included in the comparison. This ensures the metric measures *retention*, not *parsing accuracy*.
    *   **Mechanism**: The `scorer.py` module receives `visible_items` and filters the `ground_truth` before comparison.
    *   **Validation**: A dedicated test `test_hidden_masking.py` verifies that visible items are correctly excluded.
*   **Penalty**: 1.0 for each critical item (key, door) present in the hidden ground truth but missing from the agent's description.
*   **Target**: Specifically measures retention of *non-visible* history (items behind the agent).
*   **Deviation Note**: The Spec (FR-006) defines the metric using Levenshtein distance. This Plan implements Structured Diff + Semantic Similarity to ensure construct validity. A Spec Kickback has been initiated to update FR-006.

**Statistical Test (FR-005)**:
*   **Test**: One-tailed Mann-Whitney U test.
*   **Null Hypothesis (H0)**: Distributions of Memory Gap scores are equal.
*   **Alternative Hypothesis (H1)**: Text-only distribution is strictly lower (better retention).
*   **Significance**: p < 0.05.
*   **Sample Size**: Pilot: N=20 per condition. Final: N=64 per condition (if power analysis dictates).

**Statistical Power & Pilot Protocol**:
*   **Pilot Phase (N=20)**: The initial 20 runs per condition serve as a pilot to estimate variance and effect size.
*   **Power Analysis**: After the pilot, a power analysis will be conducted.
 * If the effect size is small (Cohen's d < 0.5) or variance is high, the protocol mandates scaling to N=64 per group to achieve [deferred] power.
    *   If the effect size is large (Cohen's d > 0.8) and variance is low, N=20 may be sufficient for a definitive claim.
*   **Implication**: A failure to reject H0 in the pilot phase is **inconclusive** and likely a Type II error. The plan includes a mandatory scaling step to resolve this.

## Compute Feasibility

**CPU-First Strategy**:
*   **Model**: 3B parameters quantized to 4-bit (~2GB weights + overhead).
*   **RAM**: Estimated peak ~4-5GB (model + environment + logs). Fits within 7GB limit.
*   **Time**: runs x 50 steps/run. Inference time per step is on the order of seconds on CPU. Total [deferred]. Well within 6-hour limit.
*   **GPU Escape Hatch**: Not required for 3B quantized models on CPU. If a larger model is needed, the plan will scale down to 1B or use 8-bit quantization, but the current plan is CPU-tractable.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Context Window Overflow | Agent loses history | Implement sliding window (keep last N events) or summary compression. |
| Model OOM | Crash on CI | Strict 4-bit quantization; monitor RAM usage; fallback to smaller 1B model if needed. |
| Baseline Adaptation Failure | Cannot compare | N/A (Baseline runs on Visual inputs; parser extracts structured state). |
| Hallucination | False positives in Memory Gap | Scorer includes a "false positive" penalty (US-3, SC-003). |
| Low Statistical Power | Type II Error | **Pilot Protocol**: N=20 is exploratory; Power Analysis triggers scaling to N=64 if needed. |

## References

*   **RNG-Bench Paper**: "Beyond the Current Observation: Evaluating Multimodal Large Language M..." (Primary source for Memory Gap metric and environment).
*   **Model**: Qwen2-3B-Instruct / Llama-3-8B-Instruct (Hugging Face).