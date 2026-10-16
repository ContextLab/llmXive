# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — The test run `tests/unit/test_skeleton.py` failed, reporting missing `data`, `results`, `docs`, and `contracts` directories, and the collector shows `results/` and `docs/` are absent. The required top‑level directories are therefore not all present. Create the missing `results/` and `docs/` (and ensure all required dirs are correctly placed) so the test passes.
- **T003** — The `requirements.txt` lists different packages and version pins than the `pyproject.toml` (e.g., `scipy==1.13.1` vs `1.13.0`, `matplotlib==3.9.2` vs `3.8.4`, missing `rpy2`, `goatools`, `networkx`, and extra `lxml`, `pytz`). Consequently the test that checks line‑by‑line equality would fail with the current files. The task needs a `requirements.txt` that exactly mirrors the `pyproject.toml` dependencies.
- **T004** — The required files `src/config/species.yaml` and `src/config/parameters.yaml` are reported as missing, and no YAML content is provided to confirm the required fields/values (e.g., `threshold: 0.80`, `norm_method: vst`, `seed: 42`). Consequently the task’s deliverables are not present.
- **T005** — Requested task execution failed; rerun successfully: tests/unit/test_seed_flag.py exit=1
- **T006** — Requested task execution failed; rerun successfully: src/pipeline/download_geo.py exit=1
- **T007** — Requested task execution failed; rerun successfully: code/src/pipeline/verify_samples.py exit=1
