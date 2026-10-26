# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required quickstart file is not present at `specs/001-semantic-decay-retrieval/quickstart.md` (it lives under a different specs folder), and `src/data/download.py` does not implement the prescribed `download_ego4d(output_dir: Path) -> None` using `datasets.load_dataset`; instead it uses a different signature with explicit URLs and `requests`. These deviations mean the task’s core artifacts and API contract are not met.
- **T002** — Requested task execution failed; rerun successfully: src/data/preprocess.py exit=1
