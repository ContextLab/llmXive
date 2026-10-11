# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T005** — Requested task execution failed; rerun successfully: code/main.py exit=1; code/quickstart_validation.py exit=1
- **T041** — Requested task execution failed; rerun successfully: code/validate_spatial_proxy.py exit=1
- **T006a** — The provided `code/dependency_injector.py` defines `ar1_inject` and related utilities, but it accepts any `rho` value, does not enforce the required discrete set {0, 0.1, 0.2, 0.3, 0.5}, and does not implement a dedicated vectorized AR‑resampling routine as specified. Consequently the module does not satisfy FR‑003’s restriction on strength values nor the required AR‑resampling functionality.
- **T006b-map** — The file `code/dependency_injector.py` exists and contains a `block_bootstrap` function, but the task's core requirement — the r-mapping/block-size heuristic `block_size = max(MIN_BLOCK_SIZE, int(np.sqrt(N)))` with a `MIN_BLOCK_SIZE` constant — is entirely absent: there is no `MIN_BLOCK_SIZE` constant, no `sqrt(N)`-based block size computation, and no function translating the sweep parameter r / sample size N into a block size (the existing `block_bootstrap` requires the caller to pass `block_size` directly). The implementer must add the mapping logic (e.g., a `map_r_to_block_size(N)` function
- **T006e** — declared artifact(s) missing/empty/invalid: code/sweep_config.yaml
- **T016-exec-us1** — declared artifact(s) missing/empty/invalid: results/logistic_models_us1.pkl
- **T016-exec-us2** — declared artifact(s) missing/empty/invalid: results/logistic_models_us2.pkl
- **T034** — Requested task execution failed; rerun successfully: code/quickstart_validation.py exit=1
- **T064** — declared artifact(s) missing/empty/invalid: results/config_audit.json
- **T064b** — declared artifact(s) missing/empty/invalid: data/dependency_manifest.yaml
