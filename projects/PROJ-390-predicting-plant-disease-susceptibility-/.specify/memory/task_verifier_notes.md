# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — declared artifact(s) missing/empty/invalid: data/processed/feasibility_report.md, data/processed/feasibility_gate_status.yaml
- **T001b** — declared artifact(s) missing/empty/invalid: src/ingestion/validate_labels.py, data/processed/sample_metadata.csv, data/processed/linkage_method.yaml
- **T001c** — The provided `src/ingestion/feasibility_gate_enforcer.py` is present but ends with a truncated line (`print(f"Feasibility Gate Failed: Unknown status value '{status_value}'.", file=sys.st`) causing a syntax error, so the script is not a functional implementation of the required logic. The file must be completed (e.g., finish the `print` call, close the function, and optionally call `sys.exit(main())`).
- **T002a** — No directory listings or other evidence were provided showing that the required folders (`src/`, `tests/`, `data/raw/`, `data/processed/`, `models/`, `templates/`) actually exist; without such proof the claim cannot be confirmed. The implementer must supply a file‑system snapshot, `tree` output, or similar artifact demonstrating the created directory structure.
