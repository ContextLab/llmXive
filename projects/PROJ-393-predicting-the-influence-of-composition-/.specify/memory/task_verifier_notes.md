# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `docs/reports/` directory is missing, the `requirements.txt` uses loose “>=” version specifiers instead of exact pins, and there is no execution evidence that `python -m src.main --help` produces the required “Setup OK” help message.
- **T002** — The required file `data/raw/elemental_properties_v1.csv` is missing, `src/features/descriptors.py` is absent, and `data/checksums.txt` contains no checksum entry for the CSV. Additionally, the provided test script looks for `data/raw/elemental_properties.csv` with a different column set, so it does not verify the required schema.
- **T003** — Requested task execution failed; rerun successfully: code/main.py exit=1
