# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The log only shows that `project_tree.txt` was created, but its contents are not provided, so we cannot confirm it lists the required directories (e.g., `code/utils`, `data/raw`, `results/plots`, etc.). Additionally, there is no evidence that every Python package contains an empty `__init__.py`. The implementer must supply the actual `project_tree.txt` file and verify the presence of empty `__init__.py` files in all package directories.
- **T002** — The `.ruff.toml` file matches the required configuration, but the `pyproject.toml` does not fully pin all dependencies (e.g., `python-dotenv>=1.0.0`), and there is no evidence that `pip install -r requirements.txt` was run successfully without version conflicts.
