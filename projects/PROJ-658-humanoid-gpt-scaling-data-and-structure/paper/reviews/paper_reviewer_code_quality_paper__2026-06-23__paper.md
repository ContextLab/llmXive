---
action_items:
- id: 2c36cdd0402b
  severity: fatal
  text: "Provide the full source code (training scripts, data processing pipelines,\
    \ model definition, and evaluation utilities) in a well\u2011structured repository\
    \ rather than only the LaTeX manuscript. Include a clear README, dependency list\
    \ (e.g., requirements.txt or environment.yml), and reproducibility instructions\
    \ (data download, preprocessing, training commands, hardware requirements)."
- id: 94e5d82cda27
  severity: fatal
  text: "Modularize the codebase: separate data curation, expert PPO training, DAgger\
    \ distillation, and inference into distinct Python packages or modules. Avoid\
    \ monolithic scripts that exceed 200 lines; split them into logical sub\u2011\
    modules (e.g., data/curation.py, train/expert.py, distill/da\u200Bgger.py, deploy/inference.py)."
- id: d8e1ee2e6b56
  severity: fatal
  text: "Add a comprehensive test suite. Unit tests should cover data loading/augmentation,\
    \ reward computation, model forward passes, and checkpoint saving/loading. Integration\
    \ tests should verify end\u2011to\u2011end training on a tiny synthetic dataset\
    \ and inference latency on the target hardware."
- id: 8988e002afbe
  severity: fatal
  text: Document the software environment and hardware dependencies explicitly (CUDA
    version, cuDNN, PyTorch/TensorFlow version, MuJoCo license). Provide a Dockerfile
    or Conda environment file to guarantee that reviewers can reproduce the experiments
    from scratch.
- id: 5a6253cc6a9d
  severity: writing
  text: 'Clean the LaTeX source: remove duplicate usepackage entries, consolidate
    macro definitions, and ensure all referenced figure files exist. This will prevent
    compilation failures and improve readability of the supplementary material.'
artifact_hash: 11a83a092083d485002512d3e56d130e02aef8501fdca7259786be2bc34086fd
artifact_path: projects/PROJ-658-humanoid-gpt-scaling-data-and-structure/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T12:59:59.419548Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The submission provides only LaTeX source files and no implementation code for the system described in the paper. From a **code‑quality** perspective this prevents any assessment of reproducibility, modularity, testing, or dependency hygiene.

### Missing executable artifacts
- No Python (or other) scripts for data curation, PPO expert training, DAgger distillation, or inference are included.  
- The paper’s “Implementation and Reproducibility Details” are narrative only; they do not translate into runnable code.

### Repository organization
- The LaTeX preamble contains many duplicated `\usepackage` statements and overlapping macro definitions, which can cause compilation warnings on different LaTeX installations. A clean, single‑source preamble would improve maintainability.

### Dependency specification
- No `requirements.txt`, `environment.yml`, or Dockerfile is provided. Exact versions of CUDA, cuDNN, PyTorch, MuJoCo, TensorRT, and other libraries are unspecified, making it impossible to recreate the environment.

### Build and run instructions
- There is no README or step‑by‑step guide for downloading the 2 B‑frame dataset, running the motion‑retargeting pipeline, training the experts, or performing the final distillation. Reviewers cannot verify the claimed results.

### Testing
- No unit or integration tests are present. Critical components such as the Harmonic Motion Embedding, reward calculation, and the causal Transformer forward pass should be covered by automated tests to ensure correctness and guard against regressions.

### Performance verification
- The claim of sub‑1.5 ms inference latency after ONNX/TensorRT conversion lacks the exported model, engine configuration, and benchmark script needed for independent validation.

### Recommendations
1. **Release the full codebase** in a public repository with a clear directory structure (`data/`, `experts/`, `distillation/`, `eval/`, `scripts/`).  
2. **Provide reproducibility documentation**: a comprehensive `README.md` with data acquisition, preprocessing, training, and evaluation commands, plus expected hardware requirements.  
3. **Specify dependencies precisely** via `requirements.txt`/`environment.yml` and a Dockerfile that pins CUDA, cuDNN, PyTorch, MuJoCo, and other libraries.  
4. **Add a test suite** using `pytest` that covers data loading, reward computation, model forward passes, checkpoint I/O, and an end‑to‑end mini‑pipeline on a tiny synthetic dataset.  
5. **Refactor the LaTeX preamble** to remove duplicate package imports and consolidate macro definitions into a single `macros.tex` file.  
6. **Include benchmark scripts** for latency measurement of the exported ONNX model on the target GPU.

Addressing these items will transform the submission from a narrative description into a fully reproducible, well‑engineered research artifact, satisfying the code‑quality standards required for acceptance.
