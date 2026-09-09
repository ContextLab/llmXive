# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No evidence of a `code/` directory being present (or its contents) is provided; without a visible directory or listing we cannot confirm the implementer actually created it. The required artifact is missing.
- **T001b** — No evidence was provided showing that the `data/raw/` and `data/processed/` directories actually exist; the response contains no file listings, screenshots, or commands confirming their creation. The required artifact (the two directories) is therefore missing.
- **T001c** — No evidence was provided that the `results/plots/` and `results/reports/` directories actually exist (e.g., a directory listing, command output, or screenshot). Without such proof, we cannot confirm the required directories were created.
- **T001d** — No evidence of the required `tests/unit/` and `tests/integration/` directories is provided; the artifact list contains no such paths, so we cannot verify that the directories were actually created. The implementer must add the directories (and optionally a placeholder file) to the repository.
- **T005** — declared artifact(s) missing/empty/invalid: code/config.py
- **T014** — No code, configuration, or log files were supplied that show error‑handling logic for the sieve, nor any evidence that the logging of the offending $n$ occurs before any data‑save step. Without such artifacts the requirement cannot be verified as met.
- **T013** — No `data/raw/residues_{prime}_{N}.json` file (or code that creates it) is present, and there is no evidence of JSON serialization of a `ResidueDataset`. The required output artifact is missing, so the task is not satisfied.
