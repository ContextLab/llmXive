# Research: llmXive follow-up: extending "AlayaWorld" (Synthetic Validation)

## Research Question

**Reframed**: How does the integration of a lightweight, CPU-tractable symbolic logic layer influence the long-horizon semantic consistency of a *simulated* interactive video world model (mimicking AlayaWorld mechanics with injected generative errors) compared to autoregressive generation alone?

**Scope Clarification**: This study is a **synthetic validation** of the correction mechanism. The "Semantic Drift Score" measures the efficacy of the correction logic against *injected generative errors* in the mock environment. It **does not** claim to measure the drift of the real AlayaWorld model, as the real model is unavailable. The "Mock AlayaWorld" generator is the primary experimental substrate.

## Hypothesis

The hybrid approach (Naive Generator + Symbolic Engine) will significantly reduce the "Intrinsic Drift" component of the Semantic Drift Score by at least 30% compared to the baseline (Naive Generator alone), with a p-value < 0.05, while maintaining execution within a multi-core CPU / constrained RAM constraint.

## Dataset Strategy

| Dataset | Source | Access Method | Notes |
| :--- | :--- | :--- | :--- |
| Mock AlayaWorld (Naive Generator) | Internal (Code) | Local Artifact | A deterministic mock video generator that simulates AlayaWorld behavior and *intentionally injects* generative errors (e.g., texture morphing, ghosting) to simulate real-world drift. This is the canonical source for this synthetic experiment. |
| Ground Truth Annotations | Internal (Generated) | Local JSON | A set of frames manually annotated (or generated with known state in mock) to validate the CV pipeline's accuracy. The CV accuracy is expected to be lower than a high-performance threshold due to the injected errors, which is a feature of the experiment. |

**Rationale**: The absence of a verified URL for AlayaWorld precludes a standard download. To avoid the "fatal feasibility flaw" of planning for a gated dataset, the research design pivots to a **simulation-based validation** of the correction mechanism. The "Mock AlayaWorld" generator ensures the symbolic engine's inputs (actions) and the visual output's states are perfectly aligned by design, *except* for the *intentionally injected generative errors*. This isolates the variable of interest (the correction logic) while bypassing the data access barrier. The "Semantic Drift Score" is decomposed into "Intrinsic Drift" (caused by the injected errors) and "Observational Noise" (CV error), ensuring the metric measures the model's failure to render the logic, not just CV failure.

## Methodology

### 1. Symbolic Engine (Ground Truth)
A pure Python state machine that tracks:
-   `HP` (Integer)
-   `Inventory` (List of strings)
-   `Position` (x, y coordinates)
-   `State` (Alive, Dead, Teleported)

**Rules**:
-   `Action: "hit"` -> `HP -= 10`. If `HP <= 0`, `State = "Dead"`.
-   `Action: "summon"` -> `Inventory.append("Item")`, `State = "Alive"`.
-   **Determinism**: No random seeds in the logic; output is identical for identical inputs.

### 2. Mock AlayaWorld (Naive Generator with Drift Injection)
A mock video generator that:
-   Renders frames based on the symbolic state.
-   **Intentionally injects generative errors** (e.g., texture morphing, ghosting, non-physical motion) with a known probability (e.g., [deferred]) per frame. These errors are designed to be challenging for the CV pipeline (template matching), ensuring the baseline drift is non-trivial.
-   The injected errors are *stochastic per sequence* within a seed, ensuring variance in the drift scores.
-   **Note**: This is the **primary experimental engine**, replacing the unavailable real AlayaWorld model.

### 3. Visual State Extraction (CV Pipeline)
-   **Static Objects**: Template matching (`cv2.matchTemplate`) against a reference frame.
-   **Motion**: Optical flow (`cv2.calcOpticalFlowPyrLK`) to detect movement.
-   **State Inference**: If template match score < 0.6, object is "Missing". If optical flow > threshold, object is "Moving".
-   **Validation**: Compare against the Ground Truth set.. The CV accuracy is expected to be lower than [deferred] due to the injected errors, which is a feature of the experiment, not a bug. The "Semantic Drift Score" is decomposed into "Intrinsic Drift" (caused by the injected errors) and "Observational Noise" (CV error).

### 4. Semantic Drift Score Calculation
$$ \text{Drift} = \text{Intrinsic Drift} + \text{Observational Noise} $$
Where:
-   `Intrinsic Drift` = Mismatch between Symbolic State and the *intended* visual state (before error injection).
-   `Observational Noise` = Mismatch between the *actual* visual state (with injected errors) and the CV output.
-   The "Semantic Drift Score" reported is the **Intrinsic Drift** component, which the Hybrid mode aims to reduce.

### 5. Correction Mechanism (Hybrid)
-   **Loop**:
    1.  Generate frame $t$ (with stochastic drift injection).
    2.  Extract visual state.
    3.  Compare with Symbolic State at $t$.
    4.  **If Mismatch**:
        -   Construct "Correction Token": e.g., `"Prompt: [Object] is dead and fading out."`
        -   Inject into the generation prompt for frame $t+1$ with a *probabilistic* success rate (e.g., [deferred]) to avoid deterministic perfection.
    5.  **Edge Case**: If state is "Teleported" (Visual != Logical position), log `RENDER_FAILURE` and inject "Reset" token.

### 6. Statistical Analysis
-   **Test**: Paired t-test on **Intrinsic Drift** scores (Baseline vs. Hybrid) across 10 seeds (100 pairs).
-   **Threshold**: $p < 0.05$.
-   **Effect Size**: Mean reduction ≥ 30% in **Intrinsic Drift**.
-   **Variance**: The stochastic drift injection and probabilistic correction ensure non-zero variance in the drift scores, satisfying the statistical requirements for a t-test.

## Computational Constraints & Feasibility

-   **Hardware**: 2 vCPU, 7GB RAM (GitHub Actions Free).
-   **Library Choices**:
    -   `opencv-python-headless`: No GUI, optimized for CPU.
    -   `torch` (CPU mode): No CUDA.
    -   `numpy`: Efficient array operations.
-   **Memory Strategy**: Process video frames sequentially. Do not load the full video into RAM. Use streaming for video writing.
-   **Time Limit**: minutes per 60s sequence. This requires the mock generator to be extremely fast.

## Limitations

1.  **Data Source**: The study relies on a mock generator (Mock AlayaWorld) due to the lack of a public AlayaWorld dataset. Results reflect the *logic* of the correction mechanism against *injected generative errors*, not the specific visual fidelity of the real AlayaWorld model.
2.  **CV Accuracy**: Classical CV (template matching) may fail on complex, deformed, or occluded objects. The mock generator intentionally degrades CV accuracy to test the robustness of the correction logic. The "Semantic Drift Score" is decomposed to isolate "Intrinsic Drift" from "Observational Noise".
3.  **Generalizability**: The symbolic rules are specific to the "game mechanics" simulated. They may not generalize to all video generation tasks without rule re-engineering. The results are valid for validating the *mechanism* but cannot be extrapolated to claim real-world performance without further study on actual video generation models.
4.  **Real Model Access**: This study **cannot** validate the performance of the actual AlayaWorld model due to lack of access.

## References

-   **AlayaWorld**: No verified source found. (Spec: "NO verified source found").
-   **OpenCV**: https://opencv.org/ (Standard library for template matching and optical flow).
-   **PyTorch**: https://pytorch.org/ (Used for potential model loading, though CPU-only).