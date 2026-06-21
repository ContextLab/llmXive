---
action_items:
- id: af666f32b1c9
  severity: fatal
  text: The manuscript does not provide any source code, build scripts, or environment
    specifications required to reproduce the model training and evaluation.
- id: 023f4d3d1645
  severity: fatal
  text: A public repository link with a clear, modular code layout (e.g., separate
    directories for model definition, data pipelines, training loops, inference utilities,
    and evaluation scripts) is missing.
- id: 441f853eed58
  severity: fatal
  text: No test suite or validation scripts are included to verify the correctness
    of data preprocessing, model components (ViT, MoE, DSA), or benchmark evaluation
    pipelines.
- id: fc663dc702b1
  severity: fatal
  text: Dependency declarations (e.g., requirements.txt, environment.yml, or Dockerfile)
    are absent, preventing reproducibility of the software stack.
- id: 91b89518e40f
  severity: fatal
  text: "Detailed instructions for reproducing the 256\u202FK token context experiments\u2014\
    including video I/O setup, DSA kernel compilation, and hyper\u2011parameter schedules\u2014\
    are not provided."
artifact_hash: 5db0f3878ddf869f97ae5b85f5c21e6bee16133e4d0bee899b71eabf9aaf1f3a
artifact_path: projects/PROJ-692-kwai-keye-vl-2-0-technical-report/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T09:53:02.729564Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The paper presents an impressive multimodal MoE model with 256 K token context, but from a code‑quality perspective the submission lacks any tangible software artifacts. No source files, build scripts, or environment specifications are included, making it impossible to assess readability, modularity, test coverage, or dependency hygiene. Reproducibility is a core requirement for technical reports; without a public repository or at least a zip of the codebase, readers cannot verify the reported results or extend the work.

Key deficiencies:

1. **Missing Repository Link** – The manuscript never cites a URL to a GitHub or similar hosting service. A well‑structured repository should expose top‑level modules such as `models/`, `training/`, `inference/`, and `utils/`, each with concise docstrings and type annotations.

2. **No Build or Installation Instructions** – There is no `requirements.txt`, `environment.yml`, or Dockerfile. Given the reliance on custom DSA kernels, FlashInfer, TileLang, and heterogeneous ViT‑LM parallelism, precise version pinning and compilation steps are essential.

3. **Absence of Tests** – The paper does not mention unit or integration tests for critical components (e.g., the Lightning Indexer, top‑k selection, or the MOPD distillation pipeline). A test suite would demonstrate correctness and guard against regressions.

4. **Lack of Reproducibility Details** – While the paper lists token counts, context lengths, and benchmark scores, it omits scripts to download the pre‑training data (DataComp, LAION, etc.), preprocess video frames, or run the evaluation suites (LongVideoBench, TimeLens, etc.). Reproducibility checklists or a `run.sh` wrapper are standard for large‑scale model releases.

5. **Documentation Gaps** – No README, API reference, or usage examples are provided. Users need guidance on how to invoke the model for inference (e.g., the Chunk ViT workflow) and how to reproduce the reported inference cost figures.

To bring the artifact up to community standards, the authors should release a complete, modular codebase with comprehensive documentation, a deterministic test suite, and explicit dependency specifications. Only then can the code quality be meaningfully evaluated, and the paper’s claims be independently verified.
