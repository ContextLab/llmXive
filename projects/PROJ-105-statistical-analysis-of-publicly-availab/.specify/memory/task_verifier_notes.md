# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required artifact `data/raw/2022/On_Time_Reporting_CSV.zip` is missing, and the accompanying `data/README.md` with the checksum is also absent. Moreover, the test suite shows the download step failing (no zip created). The task’s core requirement—to retrieve the full‑year 2022 BTS CSV via streaming and store the raw archive—has not been fulfilled. Fix by ensuring the download succeeds, the zip file is saved at the specified path, and a README with the correct SHA‑256 checksum is added.
- **T002** — Requested task execution failed; rerun successfully: code/preprocess.py exit=2
- **T003** — Requested task execution failed; rerun successfully: code/t003_summary.py exit=1
