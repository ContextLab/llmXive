# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — declared artifact(s) missing/empty/invalid: requirements.txt
- **T003** — declared artifact(s) missing/empty/invalid: .pre-commit-config.yaml
- **T013b-b** — The `data/results/expected_count.json` file exists and contains the required JSON key with a float value, but there is no evidence that `calculate_hardy_littlewood_expected_count(10**9)` was actually invoked or that its result was logged to the console as required by the task. A console log or execution transcript is needed to satisfy the full requirement.
- **T012** — The provided `data/raw/twin_primes.csv` exists and has the required columns, but there is no artifact showing that the implementer actually counted the rows, compared the count to the `expected_count` (3074425.688620905) within ±5%, or recorded the verification result. Likewise, there is no evidence that the file covers twin primes up to 1 000 000 000 or that a full NaN‑check on `normalized_gap` was performed. These verification steps are required by the task and are missing.
- **T014** — The evidence does not include a CSV file (e.g., `data/raw/twin_primes.csv`) containing the required columns nor any logs or measurements showing RAM usage < 2 GiB and execution time < 45 minutes. Without these artifacts, the task’s core deliverables cannot be verified.
- **T021** — Requested task execution failed; rerun successfully: code/analyze_gaps.py exit=1
