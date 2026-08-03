# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001a** — No directory listing or file tree was provided showing the existence of the required `src/` folder and its sub‑directories (`simulator`, `agents`, `pipeline`, `benchmarks`, `stats`, `utils`). Without concrete evidence that these directories were actually created, the task requirement is not satisfied. The implementer must supply a file‑system snapshot (e.g., `tree src/` output) confirming the presence of all six subfolders.
- **T001b** — The provided information contains no evidence of a `tests/` directory or the required subdirectories (`unit`, `integration`, `contract`). Without visible file system artifacts confirming their creation, the task requirement is not satisfied.
- **T001c** — No directory listing or proof that `data/raw`, `data/intermediate`, and `data/simulator_validation` exist was provided; without concrete evidence the required folder structure cannot be confirmed.
- **T001d** — No `docs/` directory or any file hierarchy was presented in the provided evidence, so the required artifact does not exist or is empty. The implementer must add the `docs/` folder with the appropriate documentation files to satisfy the task.
- **T001e** — No evidence of a `contracts/` directory or its subdirectories (`scene`, `trajectory`, `stats`) is provided; the only artifact is a textual feature specification, which does not demonstrate that the required directory structure exists or contains any files. The implementer must create the specified directories (and optionally populate them) and show their presence.
- **T003** — declared artifact(s) missing/empty/invalid: pre-commit-config.yaml
- **T005** — declared artifact(s) missing/empty/invalid: src/data_models.py, schema.yaml
- **T006** — declared artifact(s) missing/empty/invalid: src/utils/logging.py
- **T007** — declared artifact(s) missing/empty/invalid: src/config.py
- **T015** — declared artifact(s) missing/empty/invalid: src/benchmarks/loader.py
- **T012** — declared artifact(s) missing/empty/invalid: src/simulator/parser.py
- **T013** — The required file `src/simulator/noise_injector.py` does not exist in the repository, so no implementation of the noise injection functionality is present. The task cannot be considered fulfilled until this module is added with the specified behavior.
- **T014** — declared artifact(s) missing/empty/invalid: src/simulator/simulator.py
- **T016a** — declared artifact(s) missing/empty/invalid: src/stats/simulator_metrics.py
- **T016b** — declared artifact(s) missing/empty/invalid: src/stats/simulator_metrics.py
- **T017** — declared artifact(s) missing/empty/invalid: src/simulator/validator.py
- **T018a** — declared artifact(s) missing/empty/invalid: src/stats/generator_metrics.py
