---
action_items:
- id: 282bf6391f03
  severity: fatal
  text: "The submission does not include any source code, build scripts, dependency\
    \ specifications (e.g., requirements.txt, environment.yml), or test suites required\
    \ to reproduce the experiments. Provide a complete, version\u2011controlled code\
    \ repository (or a zip archive) containing the hypernetwork implementation, repository\
    \ encoder, training loops, evaluation scripts, and any data preprocessing pipelines."
- id: 5e7e1d21909f
  severity: writing
  text: "Add a clear README that documents the required hardware (GPU model, memory),\
    \ software stack (Python version, CUDA/cuDNN versions), and step\u2011by\u2011\
    step instructions to download the released dataset, install dependencies, and\
    \ run the training and evaluation pipelines from scratch."
- id: d157bca8f3b0
  severity: writing
  text: Include unit and integration tests for all major modules (e.g., encoder, hypernetwork,
    GRU recurrence, LoRA generation) and expose them via a standard test runner (pytest).
    Tests should be runnable on a minimal subset of the data to verify correctness
    without requiring the full benchmark.
- id: c7d4a8f1f16d
  severity: writing
  text: "Provide a reproducibility script (e.g., run_experiments.sh) that automates\
    \ the full end\u2011to\u2011end pipeline: data download \u2192 preprocessing \u2192\
    \ training \u2192 evaluation \u2192 result aggregation. The script should log\
    \ random seeds, hyperparameter values, and output the exact tables/figures reported\
    \ in the paper."
- id: 09db03fde074
  severity: writing
  text: "Ensure that all external resources (e.g., the Qwen3\u2011Embedding\u2011\
    0.6B model, Qwen2.5\u2011Coder\u20111.5B checkpoint) are referenced with precise\
    \ version identifiers or URLs, and include code to download them programmatically\
    \ with checksum verification."
artifact_hash: fad4da344b5e72bb204a08d5e9a960cbc3b14e42d22c2e81bf4f3bf3224fac8e
artifact_path: projects/PROJ-671-code2lora-hypernetwork-generated-adapter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:46:42.068075Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript focuses on a novel hypernetwork that generates repository‑specific LoRA adapters for code language models. While the experimental results are extensive, the review of code quality is hampered by the complete absence of any software artifacts in the submission package. As a code‑quality reviewer, I am unable to assess readability, modularity, test coverage, dependency hygiene, or reproducibility because none of these elements are present.

The paper describes several non‑trivial components (a frozen repository encoder, a hypernetwork with MLP heads, a GRU‑based recurrent module for evolution, and integration with Qwen2.5‑Coder). To evaluate these, the following are essential:

1. **Source Organization** – A hierarchical directory layout (e.g., `src/encoder/`, `src/hypernetwork/`, `src/training/`, `src/evaluation/`) with clear module boundaries. Each Python file should be under 200 lines to stay within typical token limits for review and to promote readability.

2. **Dependency Management** – A `requirements.txt` (or `environment.yml`) pinning exact package versions, especially for deep‑learning libraries (torch, transformers, accelerate) and any custom utilities. This prevents hidden version mismatches that could affect reproducibility.

3. **Testing Suite** – Unit tests for each class/function (e.g., `test_encoder.py`, `test_hypernetwork.py`, `test_gru_state.py`) and integration tests that run a short training loop on a tiny synthetic repository. Tests should be runnable with a single command (`pytest -m quick`) and must cover edge cases such as empty repositories, very large files, and malformed diffs.

4. **Reproducibility Scripts** – Scripts that automate data download (`download_data.sh`), preprocessing (`preprocess.py`), training (`train_static.py`, `train_evo.py`), and evaluation (`evaluate.py`). These should accept configuration files (YAML/JSON) so that hyperparameters can be reproduced exactly as reported in Tables 1‑3.

5. **Documentation** – A comprehensive `README.md` that explains the overall architecture, provides a quick‑start guide, and lists expected runtime and memory consumption (e.g., “training static model on 409 repos takes ~17 h on a single H100 80 GB”).

Without these artifacts, the paper’s claims cannot be independently verified, and the code quality cannot be judged. Providing the missing repository and accompanying documentation will enable a thorough assessment of modularity, readability, test coverage, and reproducibility.
