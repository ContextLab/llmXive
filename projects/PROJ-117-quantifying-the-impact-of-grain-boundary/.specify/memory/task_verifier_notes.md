# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T022** — The `interpret.py` file contains a `load_threshold_justification` function, but the required `config.yaml` file is missing, so the function cannot actually load any justification. Moreover, the snippet does not show the loaded citation being added to the final report. To complete the task, a `config.yaml` with the expected `thresholds.r2.citation` entry must be present, and the code must incorporate that value into the generated report.
