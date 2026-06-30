# MM-OCEAN CPU Adaptation: "Prejudice vs. Grounding" Mini-Benchmark

## Overview
This adaptation reproduces the core quantitative finding of the paper **"Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Personality?"** on a CPU-only, 2-core, ~7GB RAM environment.

## Core Approximation Strategy
The original paper evaluates 27 MLLMs on 1,104 videos using heavy video-LLM inference and an LLM-as-Judge for reasoning quality. This is impossible on free CI.

Instead, this adaptation:
1.  **Data Subsampling**: Uses the first **3 real video annotation files** from `data/test/` (approx. 10-15 MB of JSON metadata). It does **not** download or process video files. It relies solely on the text-based metadata (transcriptions, observations, MCQs) provided in the repo, which is sufficient to simulate the *logic* of the benchmark.
2.  **Proxy "Model"**: Replaces the 27 MLLMs with a **deterministic rule-based proxy** (a simple heuristic simulator).
    *   *Task 1 (Rating)*: Simulates a "Prejudiced" model that guesses based on keyword frequency (e.g., "smile" → High Extraversion) vs. a "Grounded" model that uses the provided observation timestamps.
    *   *Task 2 (Reasoning)*: Simulates the "Reasoning" output based on the proxy's logic path.
    *   *Task 3 (MCQs)*: Simulates answering MCQs by randomly selecting distractors vs. the correct answer to demonstrate the metric calculation.
3.  **Metric Reproduction**: Implements the **exact metrics** from `evaluate.py`:
    *   **Prejudice Rate (PR)**: % of correct ratings *not* grounded in cues.
    *   **Holistic-Grounding Rate (HR)**: % of samples where the model correctly links rating + reasoning + evidence.
    *   **MCQ Accuracy**: Standard accuracy on the 7 categories.
4.  **No GPU/Heavy Libs**: Uses only `json`, `csv`, `random`, and `statistics`. No PyTorch, TensorFlow, or HuggingFace transformers are imported.

## What is Reproduced?
*   The **Prejudice Gap** concept: Demonstrating that a model can get the right score but for the wrong reason.
*   The **Three-Tier Evaluation** logic (Rating, Reasoning, Grounding).
*   The **Failure Mode Metrics** (PR, CR, IR, HR).

## Limitations
*   This does **not** perform actual video inference. It uses the *annotations* (transcriptions/observations) as the "ground truth" context a model would see.
*   The "Model" is a heuristic simulator, not a neural network. The goal is to verify the **evaluation pipeline** and **metric calculation** logic on real data, not to benchmark a specific LLM.
