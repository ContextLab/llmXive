# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T043** — The provided `verify_quantization.py` is only partially implemented (truncated) and never loads a model or checks `model.config.quantization_config` / `model.hf_quantizer` as required. Moreover, the expected output file `data/artifacts/quantization_verification.json` does not exist. The task’s core verification and artifact generation are missing.
