# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — Checked `quickstart.md` and `configs/run.yaml` – both files exist and contain the required command description and default configuration. However, there is no evidence that `python -m src.pipeline.run_all --config configs/run.yaml` actually runs successfully, prints a concise summary, and exits with status 0; the provided test log shows a failing pytest test (NameError) and no successful execution record. A passing run (or corrected test) is needed to satisfy the verification requirement.
- **T002** — The `src/data/something_loader.py` and its unit test exist and meet the streaming, exception, and deterministic‑seed behavior, but `requirements.txt` does not pin the Faster‑RCNN detector weights (e.g., `torchvision==0.17.2`) as required. Adding that version pin will be needed to complete the task.
- **T016** — Requested task execution failed; rerun successfully: src/data/patches_download.py exit=-1 (TIMEOUT)
- **T003** — Requested task execution failed; rerun successfully: src/data/patches_download.py exit=-1 (TIMEOUT)
