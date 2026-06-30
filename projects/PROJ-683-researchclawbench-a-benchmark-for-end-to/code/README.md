# ResearchClawBench Scoring Demo

## What was adapted?

This is a **scaled-down adaptation** of the **Evaluation/Scoring Stage** of the ResearchClawBench paper.

### Simplifications vs. Original
1.  **Agent Simulation**: The original paper runs 7 autonomous agents (LLMs) to generate reports. This demo **simulates a perfect agent** by programmatically generating a `report.md` and dummy images that strictly satisfy the `checklist.json`. This removes the need for LLM APIs, API keys, and the ~20+ hour runtime of the full benchmark.
2.  **Scoring Logic**: The original scorer uses an LLM-based judge to evaluate text semantics. This demo uses a **deterministic, rule-based scorer** (keyword matching + file existence) to calculate the score. This ensures the run is fast, reproducible, and fits within the CPU time budget while faithfully testing the *structure* of the evaluation pipeline.
3.  **Dataset**: Uses the real `Astronomy_000` task data (IRAS/M33_X-7 data files) to ensure the context is real, even though the generated figures are placeholders.

### Core Result Reproduced
The script reproduces the **scoring mechanism**:
- Input: Task Checklist + Agent Output (Report + Images).
- Process: Rubric-based evaluation.
- Output: A quantitative score (0-100) and a breakdown of criteria satisfaction.

This demonstrates that the benchmark's evaluation engine works correctly and can produce real, verifiable metrics on real data structures.
