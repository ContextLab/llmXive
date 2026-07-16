# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The provided `code/preprocessing.py` is truncated (the `status` assignment line is cut off and there is no code that writes the validation DataFrame to `data/processed/proxy_validation_report.csv` or halts the pipeline on exclusions). Moreover, the required output file `data/processed/proxy_validation_report.csv` does not exist. The task’s core output and behavior are therefore not satisfied.
- **T056** — The provided `code/main.py` does not contain logic that verifies all three required sources (API, NIST, Literature) nor does it write `state/HALT_SIGNAL.yaml` when a source is missing; the literature verification function is absent and the HALT signal file is not present on disk. Consequently the task’s core requirement is unmet.
