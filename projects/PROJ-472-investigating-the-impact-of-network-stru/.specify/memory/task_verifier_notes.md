# Tasks an independent verifier REJECTED (redo these)

A separate model checked the artifacts you produced for the tasks below and judged them NOT yet complete. Each is back to `- [ ]` — REDO it so the evidence genuinely satisfies the requirement (produce the real artifact, fix the content, remove any placeholder/fabricated stand-in). Do NOT just re-check the box without changing the work.

- **T010** — The `preprocess_dMRI.py` script only contains a partial implementation (truncated after `load_tractography`) and does not perform the required `tck2connectome` conversion. Moreover, the required parcellation file `data/raw/HCP_MMP1.0_Glasser2016.zip` is absent, and the hash constant in `config.py` is a dummy placeholder, so the verification step will always fail. The task’s core requirements are therefore not satisfied.
