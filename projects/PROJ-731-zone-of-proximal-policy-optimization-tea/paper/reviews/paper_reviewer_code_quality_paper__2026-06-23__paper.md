---
action_items:
- id: c563c25e400d
  severity: writing
  text: "Supply a complete, version\u2011controlled code repository (e.g., GitHub)\
    \ containing training scripts, data preprocessing pipelines, model definition\
    \ modules, and a reproducible environment (Dockerfile or conda env) so that ZPPO\
    \ can be re\u2011run from scratch."
artifact_hash: 0fd8fa2b8ede4e304df4503c08bd0823fb3038495b7a89b759c4ee4216df60db
artifact_path: projects/PROJ-731-zone-of-proximal-policy-optimization-tea/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-23T13:03:23.392394Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The manuscript presents a sophisticated RL‑based distillation method (ZPPO) but provides virtually no software artefacts to enable reproducibility. The paper lists extensive hyper‑parameters (see Table \ref{tab:appendix:hyperparameters}) and algorithmic steps (Algorithm \ref{alg:zppo}), yet there is no accompanying source code, configuration files, or build instructions. This omission makes it impossible to verify the reported gains or to assess the quality of the implementation.

**Readability & Modularity**  
All algorithmic components (BCQ/NCQ prompt construction, replay buffer management, advantage normalization) are described only in prose and LaTeX pseudocode. Without concrete modules (e.g., `zppo/model.py`, `zppo/buffer.py`, `zppo/prompt.py`) we cannot evaluate whether the code follows clean separation of concerns, adheres to Pythonic naming conventions, or uses type hints. The lack of a clear package structure also prevents downstream users from extending or integrating ZPPO with other RL back‑ends.

**Testing**  
The paper does not mention any unit or integration tests. Critical functions such as “hard‑question detection” (`\bar{r}_x < 0.5`), candidate compression to ≤512 tokens, and buffer eviction logic (`|\mathcal{B}|_{\max}=10{,}000`) should be exercised with deterministic test cases. Absence of a test suite raises concerns about hidden bugs (e.g., off‑by‑one errors in buffer indexing) that could inflate reported performance.

**Dependency Hygiene**  
Only high‑level library choices are hinted at (AdamW, AnyPrecisionAdamW, GRPO backbone). Precise version pins for PyTorch, Transformers, and any custom RL libraries are missing. Without a `requirements.txt` or `environment.yml`, reproducing the exact FLOP counts (Table \ref{tab:appendix:compute}) is infeasible, especially given the large‑scale GPU configurations (6 student GPUs + 2 teacher GPUs per node).

**Reproducibility from Scratch**  
The paper states that training runs for 200 rollout steps and 800 gradient updates (I=4) were performed, but no random seed handling or deterministic flag settings are documented. Moreover, the “ZPPO‑77K multimodal RL corpus” (Appendix \ref{sec:appendix:dataset}) is referenced without a download URL, checksum, or data‑loader script. Researchers cannot reconstruct the exact training data distribution, which is essential for fair comparison with baselines (GRPO, Off‑Distill, etc.).

**Suggested Improvements**  
1. Publish a public repository containing:
   - `train_zppo.py` (entry point) with argument parsing for all hyper‑parameters.
   - Modular sub‑packages (`zppo/model`, `zppo/buffer`, `zppo/prompt`, `zppo/eval`).
   - A `Dockerfile` that installs exact library versions and sets deterministic CUDA flags.
2. Include a `tests/` directory with pytest suites covering prompt generation, buffer logic, and advantage computation.
3. Provide a `data/` script that downloads the ZPPO‑77K dataset, verifies its SHA‑256 hash, and preprocesses it into the format expected by the training pipeline.
4. Document random seed usage and any nondeterministic operations (e.g., mixed‑precision training) to enable exact replication of the results shown in Figures \ref{fig:appendix:buffer_compose}–\ref{fig:appendix:dynamics_scale}.

Until these software artefacts are made available, the paper’s empirical claims cannot be independently validated, and the overall code quality cannot be assessed.
