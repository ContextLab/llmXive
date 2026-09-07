# Research: llmXive follow-up: extending "MemGUI-Agent"

## Problem Statement

The "Context-as-Action" (ConAct) mechanism in mobile GUI agents folds historical context into a compact representation to manage long horizons. We hypothesize that in ultra-long horizons (50+ steps), this folding causes **information decay**, where critical cross-app dependencies (e.g., a credential entered in step 5 needed in step 60) are lost. We further hypothesize that a lightweight **semantic recall module** can retrieve these lost snippets from the raw history and inject them as "memory flashes," significantly restoring success rates without retraining the base model.

## Dataset Strategy

### Verified Sources & Feasibility Analysis

The project relies on two primary data sources:
1.  **Base Agent & Data**: The spec references **MemGUI-3K** (dataset) and **MemGUI-8B-SFT** (model).
    *   *Status*: **NOT VERIFIED** in the provided "Verified datasets" block.
    *   *Action*: The implementation will **NOT** rely on MemGUI-3K for data generation. Instead, it uses a **procedural generation engine** that constructs trajectories from state templates derived from the verified `UltraData-SFT-Agent-2609` dataset (abstracted to mobile-like semantics). This ensures the data layer is fully self-contained and not gated.
    *   *Model*: The plan assumes `MemGUI-8B-SFT` is accessible via Hugging Face. If not, the plan pivots to `microsoft/Phi-3-mini-4k-instruct` (verified open-source model). Any pivot dataset/model must be pre-verified in the "Verified datasets" block before execution.
    *   *Risk*: If the MemGUI model is not accessible, the study pivots to Phi-3. This is a valid, verified substitute.

2.  **Retrieval Model**: `sentence-transformers/all-MiniLM-L6-v2`.
    *   *Source*: Hugging Face (`sentence-transformers/all-MiniLM-L6-v2`).
    *   *Status*: **Verified** (Standard open-source model, no access restrictions).
    *   *Usage*: To generate embeddings for historical snippets and current goals.

### Synthetic Benchmark Construction (FR-001, FR-007)

Since no public dataset provides 50-100 step mobile trajectories with explicit cross-app dependencies, we must synthesize them:
1.  **Source**: Procedural generation using state templates from `UltraData-SFT-Agent-2609` (verified), abstracted to mobile UI semantics (e.g., "Settings", "Email", "Maps").
2.  **Method**:
    *   Select disjoint sub-tasks (e.g., "Open Settings", "Change WiFi", "Check Email").
    *   Inject "Dependency Links": Ensure the final step of a chain requires a parameter (e.g., a password, a specific file path) established 10+ steps ago.
    *   **Semantic Coherence Validation**: A small LLM (e.g., `Phi-3-mini`) scores each generated chain on "plausibility" (0.0–1.0). Chains scoring <0.8 are discarded and regenerated. This ensures the failure mode is 'memory decay' not 'illogical chain'.
    *   **Validation**: An automated validator checks that >95% of generated trajectories have at least one dependency link >10 steps back.
    *   **Human Review**: A subset (n=10) is reviewed for "semantic plausibility" (FR-007).

### Baseline Execution (FR-002)

*   **Model**: MemGUI-SFT (Quantized to 4-bit for CPU feasibility).
*   **Hardware**: CPU-only (GitHub Actions).
*   **Metric**: Step-by-step success rate (binary 0/1).
*   **Hypothesis Test**: Success rate drop >15% between step 30 and step 60 (descriptive).

### Semantic Recall Augmentation (FR-003, FR-004)

*   **Mechanism**:
    1.  At step $t$, extract the "current goal" from the agent's state.
    2.  Query the `all-MiniLM-L6-v2` model against a vector index of all previous steps ($0$ to $t-1$).
    3.  Retrieve top-$k$ snippets where similarity > threshold (e.g., 0.75).
    4.  Inject snippets as "Memory Flash" into the prompt.
*   **Constraint**: The query is derived **only** from the current state, not ground-truth metadata (to prevent data leakage).

### Experimental Controls (Scientific Soundness)

To isolate the "retrieval mechanism" from simply "having more text":
1.  **Negative Control (Noise Injection)**: The Recall agent runs with random noise snippets injected (same size as real snippets). Improvement over this control proves the *semantic* nature of the retrieval is effective.
2.  **Shuffled History Control**: The Recall agent retrieves from a *shuffled* history (breaking temporal logic). Improvement over this control proves the retrieval is using *relevant* context, not just any context.

### Statistical Analysis (FR-005 - Revised)

*   **Test**: **Mixed-Effects Logistic Regression (GLMM)**.
    *   *Outcome*: Binary success (0/1) per step.
    *   *Predictor*: Condition (Baseline vs. Recall vs. Noise vs. Shuffled).
    *   *Random Effects*: `trajectory_id` (to account for clustering of steps within trajectories) and `step_index` (to account for temporal decay).
    *   *Threshold*: $p < 0.05$ for significance of the Condition coefficient.
*   **Secondary**: Wilcoxon signed-rank test on aggregated rates (descriptive only, not primary).
*   **Power**: With n=30 trajectories and ~60 steps each, the GLMM has sufficient power to detect medium effect sizes in binary outcomes.

### Compute Feasibility & Escape Hatch

*   **CPU-First**:
    *   `all-MiniLM-L-v2` is small (~80MB) and runs efficiently on CPU.
    *   MemGUIB-SFT (8B parameters) on CPU:
        *   *Risk*: 8B models on CPU are extremely slow and memory-heavy.
        *   *Mitigation*: Use 4-bit quantization (`bitsandbytes` or `llama.cpp` backend via `transformers`).
        *   *Sample Size*: Reduced to 30 trajectories (max 60 steps) to fit within 7GB RAM and 6h window.
        *   *Guardrail*: `main.py` includes a memory guardrail to abort if RSS exceeds 6.5GB.
*   **GPU Escape Hatch**:
    *   If the CPU run fails due to OOM or time, the execution stage will offload to Kaggle GPU.
    *   *Note*: The plan assumes CPU is sufficient for *inference* of a quantized 8B model on a small sample. If not, the GPU escape hatch is activated.

## Decision Rationale

*   **Why Synthetic Data?** Real-world mobile datasets rarely exceed a small number of steps. To test "ultra-long" decay, we must engineer the dependency structure.
*   **Why GLMM?** Agent success rates are binary (0/1) per step, leading to non-normal distributions and hierarchical clustering. GLMM is the gold standard for this data structure.
*   **Why `all-MiniLM-L6-v2`?** It offers the best speed/accuracy trade-off for CPU-based retrieval. Larger models (e.g., `all-mpnet-base-v2`) would add unacceptable latency.
*   **Why Controls?** To prove the improvement is due to *semantic retrieval* and not just the presence of extra text or the correct answer being present in the history.