# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — Requested task execution failed; rerun successfully: code/main.py exit=1; code/quickstart_validation.py exit=1
- **T035b** — Requested task execution failed; rerun successfully: code/main.py exit=1
- **T037** — The provided `code/dependency_injector.py` generates spatial proxies with a default of `n_clusters=5` (K‑Means k=5) and the saved `spatial_proxy_report.json` records `n_clusters: 5`. The task explicitly requires using K‑Means with **k=3** (and to skip injection on failure), which is not implemented. Adjust the proxy generation to use `k=3` (or make it configurable) and ensure failure handling follows the specification.
- **T037b** — The provided `code/dependency_injector.py` contains many injection and validation utilities, but it does **not** implement the required FR‑003 mapping logic: there is no function that computes a silhouette score for the K‑Means proxy and converts it to the dependency strength `r` using `r = (silhouette_score - min_score) / (max_score - min_score)`. Adding such a mapping function (or extending an existing one) is needed to satisfy the task.
- **T041** — The provided `code/dependency_injector.py` does not compute a silhouette score nor enforce the required > 0.25 threshold, and the expected output file `data/manifests/spatial_proxy_validation.json` is missing. Consequently the FR‑003 validation logic and report generation are not satisfied.
- **T006a** — The provided `code/dependency_injector.py` defines `ar1_inject` and related utilities, but it accepts any `rho` value, does not enforce the required discrete set {0, 0.1, 0.2, 0.3, 0.5}, and does not implement a dedicated vectorized AR‑resampling routine as specified. Consequently the module does not satisfy FR‑003’s restriction on strength values nor the required AR‑resampling functionality.
- **T006e** — declared artifact(s) missing/empty/invalid: code/sweep_config.yaml
- **T016-exec-us1** — declared artifact(s) missing/empty/invalid: results/logistic_models_us1.pkl
- **T016-exec-us2** — declared artifact(s) missing/empty/invalid: results/logistic_models_us2.pkl
- **T034** — Requested task execution failed; rerun successfully: code/quickstart_validation.py exit=1
- **T064** — declared artifact(s) missing/empty/invalid: results/config_audit.json
- **T064b** — declared artifact(s) missing/empty/invalid: data/dependency_manifest.yaml
