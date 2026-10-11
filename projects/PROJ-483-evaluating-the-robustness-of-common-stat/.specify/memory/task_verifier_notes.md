# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005c** — declared artifact(s) missing/empty/invalid: data/manifests/datasets.yaml
- **T005** — Requested task execution failed; rerun successfully: code/main.py exit=1; code/quickstart_validation.py exit=1
- **T035b** — Checked `code/data_loader.py` (7 KB) – it only fetches, validates, and records checksums; it contains no logic to compute theoretical power, no reference to a replication target, and never writes a `results/power_report.json`. Moreover, the required `results/power_report.json` file is missing. The task’s core requirement (power verification and warning log) is not satisfied.
- **T037** — The provided `code/dependency_injector.py` generates spatial proxies with a default of `n_clusters=5` (K‑Means k=5) and the saved `spatial_proxy_report.json` records `n_clusters: 5`. The task explicitly requires using K‑Means with **k=3** (and to skip injection on failure), which is not implemented. Adjust the proxy generation to use `k=3` (or make it configurable) and ensure failure handling follows the specification.
- **T006e** — declared artifact(s) missing/empty/invalid: code/sweep_config.yaml
- **T016-exec-us1** — declared artifact(s) missing/empty/invalid: results/logistic_models_us1.pkl
- **T016-exec-us2** — declared artifact(s) missing/empty/invalid: results/logistic_models_us2.pkl
- **T034** — Requested task execution failed; rerun successfully: code/quickstart_validation.py exit=1
- **T064** — declared artifact(s) missing/empty/invalid: results/config_audit.json
- **T064b** — declared artifact(s) missing/empty/invalid: data/dependency_manifest.yaml
