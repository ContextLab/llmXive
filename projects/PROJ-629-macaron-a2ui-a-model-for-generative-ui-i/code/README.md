# Macaron-A2UI Adaptation: CPU-Scale Evaluation Proxy

## Purpose
This adaptation reproduces the **core quantitative evaluation logic** of the Macaron-A2UI paper (L1/L2/L3 scoring) on a **CPU-tractable scale**.

## Approximations vs. Original
1.  **Model Substitution**: The original paper uses 30B–754B models (GPU-heavy) to generate responses. This adaptation **skips generation** and instead **loads pre-cached sample outputs** (simulating the model's output) from the provided `data/eval_300` tasks. This avoids the GPU requirement while testing the *evaluation logic*.
2.  **Scoring Proxy**: The original uses an external LLM judge (e.g., GPT-4o) to score the outputs. This adaptation implements a **deterministic, rule-based proxy scorer** that checks:
    *   **L1**: JSON validity, presence of `surfaceUpdate`, schema keys.
    *   **L2**: Presence of interactive components (`SelectionList`, `TickSlider`) in the parsed structure.
    *   **L3**: Heuristic check for "text + UI" co-occurrence.
3.  **Dataset Scale**: Uses the full `data/eval_300` split (approx. 300 tasks), which is small enough for CPU processing.
4.  **No API Calls**: The original `evaluate_api_model.py` calls external APIs. This script runs entirely locally with no network dependencies.

## Artifacts
- `data/l1_scores.json`: Per-task L1 pass/fail metrics.
- `data/l2_scores.json`: Per-task L2 component presence metrics.
- `data/l3_scores.json`: Per-task L3 heuristic scores.
- `data/summary.csv`: Aggregated scores by scenario type.
- `figures/score_distribution.png`: Bar chart of scores.
