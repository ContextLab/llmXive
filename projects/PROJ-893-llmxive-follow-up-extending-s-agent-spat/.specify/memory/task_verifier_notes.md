# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T027** — The repository lacks the required `data/raw/sampled_scenes.jsonl` and the generated `data/results/vlm_trace_audit.json`. Moreover, `code/validate/vlm_audit.py` is truncated (e.g., undefined `excluded_id` and no code that writes the audit JSON), so it cannot produce the specified output. The task therefore remains unfinished.
- **T029** — The `dry_run.py` script is truncated and never writes `data/results/dry_run_status.json`; the required `constraints.schema.yaml` file is missing, and the expected output file does not exist. Consequently the validation step is not fully implemented nor does it produce the required status JSON.
