# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — The only artifact provided is a log of a successful run (`Cochrane CSV is accessible.`) and the script’s existence, but there is no evidence that the script actually raises a `FileNotFoundError` when the CSV cannot be reached, nor any CI log showing a failed step in that scenario. To satisfy the task, the implementer must supply the script’s source showing the error‑handling logic and a failing CI execution (non‑zero exit, error message) demonstrating the abort behavior.
- **T002** — Requested task execution failed; rerun successfully: code/main.py exit=2
- **T003** — The `estimate_reml` function logs failures and sets `convergence_warning=True`, but on REML failure it falls back to the DerSimonian‑Laird τ² value (`max(dl_res.tau2, MIN_POSITIVE_TAU2)`) instead of unconditionally using the required fallback τ² = 1e‑6. This violates the task specification that the fallback τ² must be exactly 1e‑6. The implementation should set `tau2 = MIN_POSITIVE_TAU2` when REML fails.
