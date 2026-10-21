# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The required outputs `data/raw/synthetic_counts.csv`, `synthetic_peaks.bed`, and `checksums.csv` do not exist on disk, so the verification criterion (run the generator, files exist non-empty) cannot be confirmed and there is no execution evidence. Additionally, the code violates the "no silent fallback" requirement: `load_schema` returns `{}` on a YAML parse error and `build_dataset_dict` skips validation entirely when the schema is empty, and the module injects `random`/`np` into `builtins` to paper over the test file's missing imports (the test's `test_file_creation` also uses `Path` without
- **T002** — Requested task execution failed; rerun successfully: code/download_encode.py exit=1
- **T003** — Requested task execution failed; rerun successfully: code/preprocess.py exit=1
