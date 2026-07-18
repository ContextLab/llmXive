# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T002** — No project files (e.g., `pyproject.toml`, `requirements.txt`, or a virtual environment) were provided, and there is no evidence that a Python 3.11 project with the listed dependencies has been created. The implementer must supply the initialized project structure and a manifest showing those packages.
- **T003** — No linting or formatting configuration files (e.g., `pyproject.toml`, `.flake8`, `ruff.toml`, or `black` settings) or documentation of their setup are present in the provided evidence. Without these artifacts, the task of configuring flake8/ruff and black cannot be verified as completed.
- **T004** — No evidence of a `data/` directory (with `raw/` and `processed/` subfolders) or a `results/` directory is provided; the claim lacks any listed files, screenshots, or directory listings to confirm the required structure exists. The implementer must create and show the actual folder hierarchy.
- **T006** — No logging configuration files, scripts, or directory structure (`logs/`) were supplied, nor any code showing distinct log levels for data ingestion warnings versus statistical results. Without such artifacts, the requirement cannot be verified as met.
- **T007** — declared artifact(s) missing/empty/invalid: schema.yaml
- **T008** — declared artifact(s) missing/empty/invalid: src/utils/checksum.py
- **T009** — declared artifact(s) missing/empty/invalid: src/data/materials.py
- **T012** — The test file `tests/contract/test_graph_schema.py` exists, but the required schema file `graph.schema.yaml` is missing, and the test imports a schema from `tests.contract.test_schemas` instead of loading `graph.schema.yaml`. Without the actual `graph.schema.yaml` the contract test cannot validate against the specified schema.
- **T012a** — declared artifact(s) missing/empty/invalid: src/data_ingestion/verify_data.py
- **T014** — The required file `src/data_ingestion/threshold.py` does not exist, and the dependent module `src/data/materials.py` is also missing, so the implementation cannot retrieve lattice constants or compute the threshold as specified. The only present artifact is `config.yaml`, which alone does not satisfy the task.
- **T016** — declared artifact(s) missing/empty/invalid: src/graphs/serializer.py, schema.yaml
- **T017** — declared artifact(s) missing/empty/invalid: src/data_ingestion/generate_synthetic.py
