# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T038** — The required artifact `code/main.py` does not exist on disk, so the pipeline cannot be executed or verified against the NHANES dataset. The task’s core requirement is therefore unmet.
- **T039** — The `outputs/correlation_results.json` file is missing, and neither `regression_results.json` nor `robustness_results.json` contain a `flags` array (let alone the required "Proxy Used: General Anxiety" entry). The task’s core verification cannot be satisfied without these artifacts.
- **T040** — The `outputs/correlation_results.json` file is missing entirely, and there is no evidence (e.g., checksums, diff output, or a statement of identical content) that the three output files were re‑run with the same seed and confirmed to be bitwise identical (or within tolerance) to a prior run. The reproducibility verification requirement is therefore not satisfied.
