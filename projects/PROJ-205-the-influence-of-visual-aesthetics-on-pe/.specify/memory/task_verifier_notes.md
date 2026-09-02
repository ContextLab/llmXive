# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T022d** — declared artifact(s) missing/empty/invalid: data/raw/submissions.csv
- **T022g** — declared artifact(s) missing/empty/invalid: data/raw/submissions.csv
- **T022h** — The repository lacks the required `data/raw/submissions.csv` and `data/raw/duplicate_audit.csv` files, and the provided `app.py` snippet is incomplete (truncated) with no concrete implementation that reads the CSV, detects duplicate `hashed_ip` values, and writes them to `duplicate_audit.csv`. The task’s core output is therefore missing.
- **T028d** — The required input file `data/raw/submissions.csv` and the output file `data/raw/duplicate_audit.csv` are both missing, so the duplicate‑detection script cannot have been executed and no audit results exist. The implementer must provide the submissions CSV and generate the duplicate audit CSV as specified.
- **T043c** — The provided `tests/benchmark/test_runtime.py` does not contain an explicit assertion checking that `data/raw/submissions.csv` is under 5 MB, and the required `data/raw/submissions.csv` file is absent from the repository. Both the assertion and the target file are needed to satisfy the task.
