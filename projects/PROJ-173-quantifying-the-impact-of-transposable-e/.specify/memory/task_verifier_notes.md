# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T003** — The evidence contains no configuration files, scripts, or documentation showing that ruff linting and black formatting have been set up (e.g., no `pyproject.toml`, `.ruff.toml`, `.pre-commit-config.yaml`, or related command/run logs). Without these artifacts, the requirement to configure linting and formatting tools is not satisfied. Adding the appropriate configuration files and proof of successful execution is needed.
- **T004** — The `generate_te_genotypes` function in `code/data_generator.py` returns a list but never writes a CSV of the raw TE genotypes, so the required raw CSV file is missing. Moreover, the presence‑frequency generation uses `random.uniform(0.01, 0.99)` and a 10 % monomorphic chance, which does not guarantee that the majority of TE frequencies lie within the required 0.05–0.95 range. The task therefore is not fully satisfied.
- **T012** — Requested task execution failed; rerun successfully: code/association.py exit=1
