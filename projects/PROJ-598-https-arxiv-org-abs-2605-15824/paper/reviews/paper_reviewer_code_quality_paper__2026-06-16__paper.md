---
action_items:
- id: 05ca85adaeca
  severity: fatal
  text: The submission does not include any source code, build scripts, or dependency
    specifications required to reproduce the reported results. Provide a publicly
    accessible repository (e.g., GitHub) containing the full training and inference
    code, with a clear README.
- id: 19cacd6ca863
  severity: fatal
  text: Current LaTeX source references many figures (e.g., figures/overall_pipeline.pdf,
    figures/analysis.pdf) but the repository lacks the corresponding source files
    (e.g., Python scripts that generate these figures). Include the data processing
    and visualization scripts.
- id: 0b2067a090e1
  severity: science
  text: "No unit or integration tests are provided for critical components such as\
    \ the KV\u2011Cache rescheduling module, the gradient\u2011reweighted DMD implementation,\
    \ or the in\u2011context teacher forcing logic. Add a test suite (e.g., pytest)\
    \ covering at least 80\u202F% of the code base."
- id: 7ea0043fcc01
  severity: writing
  text: 'Dependency hygiene is unclear: the paper mentions libraries like FSDP, AdamW,
    and specific VAE/Transformer implementations, but there is no requirements.txt
    or environment.yml. Specify exact package versions (including CUDA/cuDNN) to ensure
    reproducibility.'
- id: 5b900e4e2ee0
  severity: writing
  text: "The training hyper\u2011parameters are described in prose (e.g., learning\u2011\
    rate schedule, batch size) but not exposed in a machine\u2011readable config file.\
    \ Provide a YAML/JSON configuration that can be consumed by the training script."
- id: c321496d6d97
  severity: science
  text: "Large\u2011scale experiments (e.g., 62\u202FK samples, 23.8\u202FFPS on H200\
    \ GPU) require hardware specifications and runtime logs. Include scripts to benchmark\
    \ FPS and scripts to log GPU memory/throughput."
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-16T03:55:34.811509Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a novel video‑generation framework (FashionChameleon) but provides no concrete software artifacts. From a code‑quality perspective, the following issues prevent verification and reuse:

1. **Missing Source Code** – There is no link to a code repository, nor any `.py` files in the submission. All algorithmic components (Teacher Model, Streaming Distillation, KV‑Cache rescheduling) are described only in equations and narrative. Without source code, readers cannot inspect implementation details, verify that the described equations match the actual implementation, or extend the work.

2. **Absent Build & Dependency Information** – The paper mentions using PyTorch FSDP, bfloat16 training, and specific optimizer settings, but no `requirements.txt`, `environment.yml`, or Dockerfile is provided. This omission makes it impossible to recreate the exact software stack (e.g., CUDA version, NCCL, specific transformer libraries) required to achieve the reported 23.8 FPS on an H200 GPU.

3. **Lack of Test Coverage** – Critical modules such as the gradient‑reweighted DMD loss, the in‑context teacher forcing mask, and the KV‑Cache manipulation have no unit tests. Given the complexity of these components, a test suite is essential to catch subtle bugs (e.g., off‑by‑one errors in cache indexing) that could compromise reproducibility.

4. **No Configurable Hyper‑parameter Files** – Training schedules, learning‑rate warm‑up steps, and cache size `M=23` are embedded in the text. Providing a structured configuration (YAML/JSON) that the training script reads would improve readability, allow easy hyper‑parameter sweeps, and reduce the risk of transcription errors.

5. **Reproducibility of Figures & Metrics** – Figures such as Figure 2 (overall pipeline) and the quantitative tables rely on scripts that process the curated dataset and compute metrics (Cur, GME, etc.). The absence of these scripts, as well as the raw metric logs, hampers verification of the claimed improvements (e.g., 30–180× speedup).

6. **Documentation & Usage Examples** – Even if the code were supplied, the paper currently lacks a quick‑start guide, example command‑line invocations, or sample data splits. Clear documentation is vital for external researchers to reproduce the short‑video (81‑frame) and long‑video (165‑frame) experiments.

**Recommendation:** The authors should release a complete, well‑structured codebase with the following elements:

- `src/` directory containing modular implementations (`models/teacher.py`, `distillation/grad_reweight.py`, `kv_cache/reschedule.py`).
- Test suite under `tests/` with coverage reports.
- Dependency specifications (`requirements.txt` + optional `Dockerfile`).
- Config files (`configs/train.yaml`, `configs/distill.yaml`) mirroring the hyper‑parameters described in Sections 4–5.
- Scripts to generate each figure and table (e.g., `scripts/eval_metrics.py`, `scripts/plot_fps.py`).
- A README detailing hardware requirements, data preparation steps (including the 62 K curated triplets), and instructions to reproduce the main results.

Providing these artifacts will address the fatal reproducibility concerns and enable the community to validate and build upon the proposed FashionChameleon system.
