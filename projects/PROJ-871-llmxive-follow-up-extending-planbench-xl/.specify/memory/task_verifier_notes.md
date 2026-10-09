# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required directories `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/code/`, `data/`, and `tests/` do exist, but they are populated with many files and sub‑folders rather than being empty as the task specifies. The artifact therefore does not meet the “empty directories” requirement. The implementer must provide truly empty `code/`, `data/`, and `tests/` directories (or at least no files beyond the required placeholder structure).
- **T002** — The provided `requirements.txt` matches the requested pinned versions, but the required `requirements_checksum.txt` (containing the SHA‑256 checksum) and the `setup_log.txt` showing a successful `pip install -r requirements.txt` and `pip list` are absent. Without these verification artifacts the task is not fully satisfied.
- **T003** — The required `.gitignore` file at `projects/PROJ-871-llmxive-follow-up-extending-planbench-xl/.gitignore` is not present in the provided artifacts, and therefore its contents cannot be verified. The implementer must add the file with the specified ignore patterns.
- **T004** — The `setup_log.txt` file exists but only shows pip install output; it does not contain the required `python --version` line nor the `pip list` output showing a non‑empty package list. The verification output is therefore missing.
- **T005** — Requested task execution failed; rerun successfully: code/dataset/loader.py exit=1
- **T006** — Requested task execution failed; rerun successfully: code/dataset/extractor.py exit=1
