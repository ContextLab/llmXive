---
action_items:
- id: dc12fa7a8322
  severity: science
  text: Appendix app:implementation lacks specific random seeds and library version
    pinning, hindering exact reproducibility of RL training dynamics.
- id: f68e0dd6038d
  severity: science
  text: RQ-VAE training details in Appendix app:semantic are high-level; provide config
    files or scripts for the quantization layer and codebook size.
- id: ecbf355d4ae8
  severity: science
  text: Feasibility Oracle instantiation (KG vs LLM) in Appendix app:data_process
    needs explicit prompt templates or KG schema definitions.
artifact_hash: 04be55bc6e5d8d960cc49a3798cf6dcfe7112c356a8019a56a3a1b07b8b8ef6d
artifact_path: projects/PROJ-640-https-arxiv-org-abs-2605-28293/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-01T21:55:24.982141Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

This review evaluates the reproducibility and implementation clarity of the ProRL framework as described in the manuscript. While the paper claims code availability at `github.com/hongruhou89/ProRL`, external repositories cannot be accessed during this review. Consequently, the assessment relies on the textual description of the code artifacts within the LaTeX source.

The Appendix `app:implementation` provides a comprehensive hyperparameter table (Table `tab:hyperparameters_grouped`), which is commendable. However, critical reproducibility details are absent. Specifically, random seeds for data splitting, model initialization, and RL rollout sampling are not specified. Without these, the stochastic nature of the policy gradient updates (Section `sec:method`) cannot be replicated exactly. Additionally, dependency hygiene is not addressed; no `requirements.txt` or `pyproject.toml` is included in the text, leaving library versions (e.g., PyTorch, RecBole, Transformers) ambiguous.

In Appendix `app:data_process`, the "Smooth Guided Data Construction" relies on a "Feasibility Oracle." The distinction between Knowledge Graph and LLM instantiations is described conceptually, but the exact prompt templates for the LLM oracle or the specific KG schema used are missing. This ambiguity prevents independent verification of the data quality claims. Furthermore, the RQ-VAE training in Appendix `app:semantic` specifies architecture sizes (e.g., 5 levels, 128 codebook) but lacks the loss weighting schedule or optimizer state details beyond basic learning rates.

For the paper to support full reproducibility from scratch, the authors must ensure their repository includes a `Dockerfile` or `environment.yml`, explicit random seeds in the training scripts, and the exact prompt templates used for the Feasibility Oracle. The current textual description is sufficient for understanding the methodology but insufficient for independent code implementation.
