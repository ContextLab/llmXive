# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T000#1** — The `verify_scope.py` script is truncated and does not contain the logic to write `data/artifacts/scope_change_record.json`. Moreover, the required JSON output file is missing from the repository. The task’s core requirement—producing the approved scope change record—is therefore not satisfied.
- **T001** — The required `data/artifacts/scope_change_record.json` file is missing, and `code/data/generate_config.py` is truncated (ends with an orphan “r”) and never writes `code/config.yaml`. Consequently the script does not fulfill the specified logic, even though a `code/config.yaml` file is present. The task needs a complete `generate_config.py` that reads the JSON, checks `approved`, and writes the config, plus the missing scope record JSON.
