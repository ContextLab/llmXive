# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T024a** — The repository lacks the required `data/processed/embeddings.json` output file, and `prompt_gen.py` does not write any embeddings to that location. Moreover, the code defaults to the model `"all-MiniLM-L6-v2"` instead of the specified `"sentence-transformers/all-MiniLM-L-v"`, and the curvature‑calculation function is truncated, indicating an unfinished implementation.
- **T024b** — The `prompt_gen.py` file contains a partially‑implemented `calculate_curvature` function, but the `calculate_all_curvature_scores` method is truncated and never writes the results to `data/processed/curvature_scores.json`. Moreover, the required `curvature_scores.json` file does not exist. The task’s core output is therefore missing.
