# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T036** — No evidence of modified `src/tracing.py` or `src/benchmark.py` was provided; the claimed “Data Source Verification” logging step is absent, so the required artifact does not exist.
- **T037** — No evidence of a modified `src/tracing.py` is present; there is no code showing batch‑size‑1 processing, memory‑profiling logic, or logging of memory peaks after each image, so the required refactor has not been demonstrated.
- **T038** — The required output file `data/results/null_hypothesis_flag.json` does not exist, indicating that the validation task was not implemented (no warning flag is being written). Additionally, there is no evidence that `src/clustering.py` was modified to perform the silhouette‑score check and generate the warning. The implementer must add the validation logic and ensure the JSON flag file is created when the score is below 0.25.
