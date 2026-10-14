# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Requested task execution failed; rerun successfully: code/run_experiments.py exit=1
- **T002** — Requested task execution failed; rerun successfully: code/data.py exit=1
- **T003** — The test run failed (exit 1): `hf_hub_download` for `author/lightdiff-100m` returned 401 Repository Not Found, so no real model was ever downloaded or loaded, and `outputs/model_checkpoint.json` is MISSING. Moreover, `code/model.py` wraps the checkpoint in an `_IdentityDiffusionModel` whose `forward` just returns the input — an explicit placeholder, not a real ≤100M-parameter discrete diffusion model — and there is no evidence of a successful CPU forward pass or the "Model loaded on CPU" log. The implementer must use an actual existing HuggingFace discrete-diffusion checkpoint, load its real a
- **T004** — Requested task execution failed; rerun successfully: code/data.py exit=1; code/run_experiments.py exit=1
