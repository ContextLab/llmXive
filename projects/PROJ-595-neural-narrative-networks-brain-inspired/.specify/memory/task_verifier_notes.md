# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The task requires five directories to be created: `code/`, `data/raw/`, `data/processed/`, `data/results/`, and `tests/`. While `code/` and `tests/` directories exist with content, three required directories are **MISSING**: `data/raw/`, `data/processed/`, and `data/results/`. The `code/__init__.py` file exists and is non-empty (51 bytes), satisfying that requirement. However, the `.gitignore` file is not mentioned in the evidence and appears to be missing. The task explicitly requires creating these five directories and a `.gitignore` file as foundational project structure; partial completion
- **T006** — The task requires implementing `code/utils/schema_validation.py` with validators for neural, text, and RSA contracts. While the file exists and contains substantial code with three public validator functions (`validate_neural_data`, `validate_text_data`, `validate_rsa_output`), the implementation is **non-functional** because it depends on schema files that do not exist.

The code attempts to load YAML schema files from `SCHEMA_DIRS` (either `contracts/` or `specs/schemas/` directories) using `_load_schema()`. The three required schemas are:
- `neural-data.schema.yaml`
- `text-data.schema.yaml
