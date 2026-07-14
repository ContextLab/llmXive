# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T013** — The required `data/processed/baseline_metrics.json` file is missing, so no baseline metrics have been recorded, let alone with ≥3‑decimal precision for ≥10 datasets. The task’s core deliverable is absent.
- **T023** — The required output file `data/processed/cleaned_metrics.json` does not exist on disk. Although `code/analysis.py` is present, there is no evidence that it was executed to generate the cleaned‑variant metrics or that the expected JSON file was created. The missing artifact must be produced for the task to be considered complete.
- **T027** — The provided `code/reporting.py` is truncated (ends with `diff[ds`), lacks any implementation for the required “inconsistency rate” metric, and does not expose a function that returns it. Moreover, the claimed dependent artifacts `data/processed/cleaned_metrics.json` and `data/processed/baseline_metrics.json` are not present in the evidence. Consequently the task’s full requirements are not satisfied.
