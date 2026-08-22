# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T004b** — The required file `src/data/verify_provenance.py` does not exist, so no provenance‑checking logic, JSON output, or exit‑code behavior is present. The task cannot be considered fulfilled until this script is created and implements the specified checks.
- **T019** — The provided `src/models/evaluate.py` only defines generic MSE/RMSE helpers and a CSV writer, but it does not compute per‑dimension baseline results, does not calculate R², does not implement the validation against the best model from T015, nor does it exit with code 1 on failure. Moreover, the required output file `data/baseline_results.csv` is missing. The task’s core requirements are therefore unmet.
- **T017** — declared artifact(s) missing/empty/invalid: src/reports/generate.py
- **T018** — declared artifact(s) missing/empty/invalid: data/dimension_viability.csv
- **T024** — The repository lacks the required `data/timing_profile.csv` file, and the shown portion of `src/models/evaluate.py` is truncated before any logic that writes the projected total hours to that CSV. Consequently, the task’s output artifact is missing and the implementation is not verifiable as complete.
