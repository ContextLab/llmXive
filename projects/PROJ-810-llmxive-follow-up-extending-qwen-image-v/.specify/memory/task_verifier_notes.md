# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `code/boot/verify_resources.py` – it HEAD‑checks the dataset URL correctly but uses a different model URL (`https://huggingface.co/hf-internal-testing/tiny-vae`) instead of the required `https://huggingface.co/Qwen/Qwen-Image-VAE-2.0`. The script therefore does not satisfy the task’s specification to verify that exact VAE model URL. The `quickstart.md` does contain the required command line, but the primary verification script is incorrect. The model URL check must be updated to the specified Qwen‑Image‑VAE‑2.0 URL.
- **T003** — Checked `code/utils/logger.py` – it defines `get_logger` and seeds `random`, `numpy`, and `torch` on import. However, the required output file `data/raw/logger_init.json` is missing, so the seed‑recording part of the task is not satisfied. The logger works but the verification artifact does not exist.
- **T005** — Requested task execution failed; rerun successfully: code/analysis/runtime_estimate.py exit=1
