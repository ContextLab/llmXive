# User Stories

## US1: Construct Text-Based Scene Simulator

**Goal**: Implement a deterministic text-based simulator that converts image prompts into structured JSON scene descriptions with controllable "Noisy Mode".

**Acceptance Criteria**:
- Simulator accepts a prompt and mode flag ("Perfect" or "Noisy").
- Returns valid JSON with `objects`, `relationships`, and `attributes`.
- No external image generation API calls.
- Response time < 500ms.
- Noise injection falls within 5-15% target range.

## US2: Execute CPU-Tractable Agentic Loop

**Goal**: Execute the full agentic pipeline (Planner → Generator → Critic → Planner) using a lightweight LLM on CPU.

**Acceptance Criteria**:
- Processes benchmark samples from WISE/RISE.
- Completes the loop within 6 hours on CPU.
- RAM usage ≤ 7GB.
- Outputs JSON log of reasoning scores (F1-score).

## US3: Perform Statistical Comparison and Ablation

**Goal**: Perform statistical analysis and ablation study to quantify the value of structural decomposition.

**Acceptance Criteria**:
- Outputs report with p-values and effect sizes (Cohen's d).
- Compares "Full Loop" vs. "No-Critic Loop".
- Validates statistical power (sample size N).
- Handles missing image-based baselines by falling back to text-only comparison.
