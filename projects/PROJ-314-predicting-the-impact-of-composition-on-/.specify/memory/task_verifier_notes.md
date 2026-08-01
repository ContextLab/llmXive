# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T012a** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T012b** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T017b** — The `generate_data_availability_report()` function is present and writes the required fields, but the expected output file `data/reports/data_availability_report.json` does not exist on disk (the directory may be missing, causing a write failure). Consequently the task’s core requirement—producing the JSON report before halting—is not satisfied. The implementer must ensure the `data/reports` directory is created (or use a safe path) and that the function is actually executed so the file is written.
