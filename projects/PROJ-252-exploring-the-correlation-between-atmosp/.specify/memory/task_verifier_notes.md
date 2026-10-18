# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T001** — `requirements.txt` is not fully pinned: its first 15 lines list unpinned packages (`pandas`, `numpy`, `scipy`, `scikit-learn`, `requests`, `tqdm` ×3, `pyyaml`, `datasets`, `statsmodels`, `memory_profiler`, `huggingface_hub`, `xarray`, `netCDF4`) before the pinned block, so `pip install -r requirements.txt` would install unpinned versions and fail the "no unpinned warnings" verification; it also contains duplicate entries and a stray comment. The file must contain only the exact version pins (e.g., `numpy==1.26.4`, ..., `huggingface_hub==0.23.0`) with no bare package names. `code/seed_init.py`
- **T002** — Requested task execution failed; rerun successfully: code/download.py exit=1
