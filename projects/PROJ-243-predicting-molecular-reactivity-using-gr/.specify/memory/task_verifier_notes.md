# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The evidence provided does not show the six required directories (`data/raw`, `data/processed`, `data/assets`, `code`, `artifacts`, `tests`) nor the `.gitkeep` files inside each; no file listings or directory structures are present to confirm they exist. The implementer must add these directories with a `.gitkeep` file in each and provide evidence (e.g., `git ls-files` output) that they are tracked.
- **T002** — Requested task execution failed; rerun successfully: code/run_lint.sh exit=1
- **T003** — The required `data/raw/checksums_schema.yaml` file is missing, and the `data/raw/checksums.json` file is not empty (it contains checksum data) whereas the task demanded an empty JSON file. Both artifacts must exist and meet the specified content criteria.
- **T005** — Requested task execution failed; rerun successfully: code/data/curate_reference_substructures.py exit=1
