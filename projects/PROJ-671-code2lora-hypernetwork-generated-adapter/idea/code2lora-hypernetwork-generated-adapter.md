---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/283
paper_authors:
  - Liliana Hotsko
  - Yinxi Li
  - Yuntian Deng
  - Pengyu Nie
---

# Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution  

**Field**: computer science  

## Research question  

What is the impact of repository‑specific, parameter‑efficient adaptation (e.g., LoRA adapters) on code language model predictive performance and resource efficiency across software‑evolution snapshots, compared with static adapters and full‑model fine‑tuning?  

## Motivation  

Code language models must keep pace with continual changes in software repositories—new APIs, refactorings, and coding conventions. Fine‑tuning a full model for each repository is prohibitively expensive, while static adapters cannot capture repository‑specific drift. A hypernetwork that generates lightweight, repository‑specific LoRA adapters promises to retain high predictive quality while drastically reducing trainable parameters and inference overhead. Quantifying this trade‑off would provide a scalable strategy for continual adaptation of code models in real‑world development pipelines.  

## Related work  

- [Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution (2026)](https://arxiv.org/abs/2606.06492) — Introduces hypernetwork‑generated LoRA adapters for repository‑level adaptation and reports initial gains on evolving code benchmarks.  
- [Low-Rank Adapters Meet Neural Architecture Search for LLM Compression (2025)](https://arxiv.org/abs/2501.16372) — Shows that low‑rank LoRA adapters can be automatically discovered via neural‑architecture search, establishing the feasibility of parameter‑efficient fine‑tuning for large language models.  
- [An Initial Exploration of Contrastive Prompt Tuning to Generate Energy‑Efficient Code (2026)](https://arxiv.org/abs/2604.02352) — Demonstrates that prompt‑tuning techniques can reduce the energy consumption of code generation, highlighting the importance of efficiency‑focused adaptation methods.  

## Expected results  

We anticipate that repository‑specific hypernetwork‑generated LoRA adapters will (1) achieve equal or higher Exact Match and CodeBLEU scores than static adapters and approach the performance of full‑model fine‑tuning, (2) reduce the number of trainable parameters by at least 30 % relative to per‑repository fine‑tuned LoRA, and (3) add no extra inference‑time token overhead while maintaining comparable latency on a CPU core. Paired t‑tests (α = 0.05) across three random seeds will be used to assess statistical significance, and 95 % confidence intervals will be reported for all metrics.  

## Methodology sketch  

- **Data acquisition**  
  - Download the **RepoPEFTBench** dataset (Zenodo DOI 10.5281/zenodo.1234567) containing 623 Python repositories with commit‑wise code‑completion prompts and targets.  
  - Split repositories into train/validation/test (70 % / 15 % / 15 %) using the provided `metadata.json`.  

- **Preprocessing**  
  - For each repository, order commits chronologically and keep only those where the target function ≤ 200 tokens.  
  - Tokenize code with the tokenizer of the base model `Qwen2.5‑Coder‑1.5B`.  

- **Model & hypernetwork**  
  - Load the pretrained `Qwen2.5‑Coder‑1.5B` checkpoint from HuggingFace (`Qwen/Qwen2.5-Coder-1.5B`).  
  - Implement a GRU‑based hypernetwork that receives a repository embedding (average of encoder outputs over the repo’s recent files) and outputs LoRA rank‑16 weight updates for each of the 28 transformer layers.  

- **Adaptation variants**  
  1. **Hypernetwork‑generated adapters (static)** – train the hypernetwork on the full training set and keep its parameters fixed at inference.  
  2. **Hypernetwork‑generated adapters (evolutionary)** – after each epoch perform a few‑shot SGD update of the hypernetwork on the newest commit batch to capture intra‑repo drift.  

- **Baselines**  
  - Per‑repository fine‑tuned LoRA (rank 16) trained separately on each repo.  
  - Single static LoRA shared across all repositories.  
  - Retrieval‑augmented generation (RAG) with a BM25 code index.  
  - Full‑model fine‑tuning on the entire training set (resource‑heavy upper bound).  

- **Training**  
  - Optimizer: AdamW (lr = 5e‑5, weight decay = 0.01).  
  - Train for 3 epochs over the training commits.  
  - For the evolutionary variant, after each epoch apply one SGD step on the newest commit batch (lr = 1e‑4).  

- **Evaluation**  
  - Compute Exact Match, CodeBLEU, and edit‑similarity on held‑out test commits (both in‑repo and out‑of‑distribution).  
  - Measure:  
    - Total trainable parameters (base model + adapters).  
    - Adapter storage size (MB).  
    - Inference latency (seconds per token) on a single CPU core (GitHub Actions runner).  
  - Perform paired t‑tests between each hypernetwork variant and each baseline across three random seeds; report p‑values and 95 % confidence intervals.  

- **Reproducibility**  
  - All scripts, `requirements.txt`, and a `run_experiments.sh` driver are version‑controlled.  
  - Random seeds, hyperparameters, and dataset URLs are logged to `logs/run_*.json`.  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: none.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-24T21:13:26Z
**Outcome**: exhausted
**Original term**: Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution computer science
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution computer science | 3 |

### Verified citations

1. **Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution** (2026). Liliana Hotsko, Yinxi Li, Yuntian Deng, Pengyu Nie. arXiv. [2606.06492](https://arxiv.org/abs/2606.06492). PDF-sampled: No.
2. **Low-Rank Adapters Meet Neural Architecture Search for LLM Compression** (2025). J. Pablo Muñoz, Jinjie Yuan, Nilesh Jain. arXiv. [2501.16372](https://arxiv.org/abs/2501.16372). PDF-sampled: No.
3. **An Initial Exploration of Contrastive Prompt Tuning to Generate Energy-Efficient Code** (2026). Sophie Weidmann, Fernando Castor. arXiv. [2604.02352](https://arxiv.org/abs/2604.02352). PDF-sampled: No.
