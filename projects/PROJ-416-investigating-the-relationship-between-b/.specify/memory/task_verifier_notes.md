# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T015** — The repository lacks the required `data/metrics/network_metrics.csv` file, and the shown portion of `code/data/preprocess.py` does not contain any logic that writes the calculated FD to that CSV (or conditionally excludes subjects). Consequently, the task’s core requirement—to save FD as a mandatory covariate only for subjects passing the motion threshold—is not fulfilled.
- **T017** — The repository contains `code/data/save_metadata.py`, but the file is truncated and does not clearly show logic that writes the required `data/metrics/subject_info.json`. Moreover, the expected output file `data/metrics/subject_info.json` is absent from the project. Without the JSON file being generated (or code that reliably creates it), the task’s requirement is not satisfied.
- **T031** — The `stats.py` file is truncated and does not contain the required logic for halting when N < 5, flagging when 5 ≤ N < 10, computing and storing the minimum N, writing it to `data/metrics/statistical_results.csv`, or generating a G*Power report snippet. Moreover, the expected CSV file is missing entirely.
- **T035** — declared artifact(s) missing/empty/invalid: data/metrics/statistical_results.csv
