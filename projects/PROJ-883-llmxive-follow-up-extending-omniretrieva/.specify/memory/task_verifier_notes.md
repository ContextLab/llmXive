# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/main.py exit=1
- **T002** — The four required schema files (`query_instance.schema.yaml`, `execution_log.schema.yaml`, `execution_metric.schema.yaml`, `statistics-result.schema.yaml`) are all reported MISSING by the collector, and the recorded pytest run of `tests/unit/test_contracts.py` failed with "Schema file query_instance.schema.yaml missing". Additionally, the deprecated `analysis_result.schema.yaml` and `gam_results.schema.yaml` and the legacy `execution_metrics.schema.yaml` still appear in the contracts directory listing, so the cleanup portion was not done either.
