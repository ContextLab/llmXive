# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — The file `src/utils/logging.py` is present and implements generic logging utilities, but it does not contain any logic, functions, or documentation specifically for tracking skipped invalid SMILES as the task requires. A concrete mechanism (e.g., a logger or helper that records when a SMILES string is invalid) is missing.
- **T007** — The required files `specs/001-predicting-molecular-reactivity-using-gr/contracts/reaction_record.schema.yaml` and `specs/001-predicting-molecular-reactivity-using-gr/contracts/molecular_graph.schema.yaml` are reported as MISSING, so the schemas were not created.
- **T008** — the task writes platform-owned path(s) inside the project: `.github/workflows/ci.yml` (shadows `.github/`). A project owns data/, figures/, code/ and paper/; the platform owns state/ and derives artifact hashes at verification time. Re-scope the step to write only project-owned outputs.
