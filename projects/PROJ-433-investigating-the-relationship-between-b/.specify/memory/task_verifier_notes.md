# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The `data/metrics_log.txt` file is missing, and there is no evidence that the required directories (`data/raw`, `data/processed`, `data/results`, `code`, `tests`, `contracts`) were actually created. The task’s directory‑structure requirement is therefore not fully satisfied.
- **T002** — No artifact (e.g., test script, log output, or directory listing) was provided to demonstrate that the required folders have been created and asserted. Without concrete evidence of directory existence checks, the claim cannot be verified. The implementer must supply the code or output that creates the directories and asserts their presence.
- **T003** — No `README.md` file or its contents were provided; without the actual placeholder document we cannot confirm that installation, usage, and reproducibility sections exist. The required artifact is missing.
- **T004** — No `venv/` directory or activation script (e.g., `venv/bin/activate` or `venv/Scripts/activate`) was presented in the provided artifacts, so the required virtual environment cannot be confirmed as created. The implementer must supply the actual `venv/` folder with the activation script.
- **T006** — The repository contains `data/preprocess_log.txt` and `data/analysis_log.txt`, but both files are populated with log entries rather than being empty, and the required `data/metrics_log.txt` file is completely missing. The task demanded three empty log files, which is not satisfied.
- **T007** — The `contracts/` directory with the three `.schema.yaml` files exists, but no evidence is provided showing the files contain actual JSON‑Schema skeletons (they could be empty or placeholders). The implementer must supply the file contents to confirm they define minimal JSON‑Schema structures for dataset, metric, and result.
- **T008** — The provided `requirements.txt` contains the correct pinned versions, but it resides in `code/requirements.txt` rather than at the repository’s top level as the task specifies. Relocate or duplicate the file to the project root so it is truly top‑level.
- **T009** — The provided `requirements.txt` exists, is non‑empty, and all dependencies are pinned with `==` versions. However, there is no evidence that the implementer actually ran `pip install -r requirements.txt` and confirmed that `import nilearn` (or other imports) succeeds, which is a required part of the task. The import‑success verification is missing.
- **T010** — No linting or formatting configuration files (e.g., `.ruff.toml`, `pyproject.toml` with Black settings) or installation scripts are present in the provided evidence, so the requirement to install ruff/black and ensure their config files exist is not satisfied.
- **T036** — declared artifact(s) missing/empty/invalid: data/analysis_log.txt
- **T051** — declared artifact(s) missing/empty/invalid: data/metrics_log.txt
- **T059** — declared artifact(s) missing/empty/invalid: data/analysis_log.txt
- **T063** — declared artifact(s) missing/empty/invalid: data/analysis_results.tsv
- **T069** — declared artifact(s) missing/empty/invalid: data/analysis_log.txt
- **T073** — declared artifact(s) missing/empty/invalid: data/results/permutation_results.tsv
- **T076** — declared artifact(s) missing/empty/invalid: data/results/permutation_report.png
- **T078** — declared artifact(s) missing/empty/invalid: data/analysis_log.txt
- **T088** — declared artifact(s) missing/empty/invalid: tests/edge_cases/
- **T091** — declared artifact(s) missing/empty/invalid: .github/workflows/ci.yml
