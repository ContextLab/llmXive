# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T033a** — No evidence of a `README.md` file (or its contents) was presented, so we cannot confirm that it was updated with a pipeline overview and usage instructions as required. The implementer must provide the actual README file showing the requested documentation.
- **T034** — The required artifact `results/timing_report.json` is missing, so there is no evidence that the pipeline was executed or that the 6‑hour CPU limit was respected. The task’s verification condition is not satisfied.
- **T034a** — The repository contains `code/timing.py`, but the file ends abruptly (the `save_timing_report` function is incomplete) and there is no evidence that it writes `results/timing_report.json`. Moreover, the expected output file `results/timing_report.json` is absent from the project. The required timing report is therefore not generated.
