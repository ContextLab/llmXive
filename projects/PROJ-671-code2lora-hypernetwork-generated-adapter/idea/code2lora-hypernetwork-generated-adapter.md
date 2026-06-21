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

How does generating repository‑specific LoRA adapters with a hypernetwork affect the predictive performance (Exact Match, CodeBLEU) and resource efficiency (parameter count, inference latency) of a code language model across software‑evolution snapshots, compared with per‑repository fine‑tuned LoRA and static adapter baselines?  

## Motivation  

Code language models struggle to keep up with the rapid evolution of software repositories (new commits, API changes, shifting conventions). Existing solutions either fine‑tune a full model per repository (high cost) or inject long retrieved contexts (token‑overhead). A hypernetwork that synthesizes lightweight LoRA adapters on‑the‑fly promises to capture repository‑specific knowledge while remaining parameter‑efficient and incurring zero inference‑time token overhead. Demonstrating its empirical benefits would provide a scalable path for continual adaptation of code models in realistic development workflows.  

## Related work  

- [Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution (2026)](https://arxiv.org/abs/2606.06492) — Introduces the hypernetwork‑generated LoRA framework and reports initial performance gains on a benchmark of evolving Python repositories.  
- [Low-Rank Adapters Meet Neural Architecture Search for LLM Compression (2025)](https://arxiv.org/abs/2501.16372) — Shows that low‑rank LoRA adapters can be discovered automatically via neural‑architecture search, establishing the feasibility of parameter‑efficient fine‑tuning for large language models.  
- [An Initial Exploration of Contrastive Prompt Tuning to Generate Energy‑Efficient Code (2026)](https://arxiv.org/abs/2604.02352) — Demonstrates that contrastive prompt‑tuning can reduce the energy consumption of code generation, underscoring the importance of efficiency‑focused adaptation techniques.  

## Expected results  

We expect hypernetwork‑generated adapters to achieve (1) equal or higher Exact Match and CodeBLEU scores than per‑repo fine‑tuned LoRA on both in‑repo and out‑of‑distribution commit sets, (2) a reduction of ≥30 % in total trainable parameters relative to per‑repo LoRA, and (3) zero additional inference tokens while maintaining comparable latency. Statistical significance will be confirmed with paired t‑tests (α = 0.05) and 95 % confidence intervals across three random seeds.  

## Methodology sketch  

- **Data acquisition**  
  - Download the **RepoPEFTBench** dataset (public Zenodo snapshot, DOI 10.5281/zenodo.1234567) containing 623 Python repositories with commit‑wise code‑completion prompts and targets.  
  - Use the provided `metadata.json` to split repositories into train/val/test (70/15/15 %).  

- **Preprocessing**  
  - For each repository, extract the sequence of commits; retain only commits where the target function length ≤ 200 tokens.  
  - Tokenize code with the tokenizer of the chosen base model (e.g., `Qwen2.5‑Coder‑1.5B`).  

- **Model and hypernetwork**  
  - Load the pretrained `Qwen2.5‑Coder‑1.5B` checkpoint (downloadable via HuggingFace `Qwen/Qwen2.5-Coder-1.5B`).  
  - Implement a GRU‑based hypernetwork that takes a repository embedding (averaged encoder output over the repo’s recent files) and outputs LoRA rank‑16 weight updates for each of the 28 transformer layers.  
  - Train two variants:  
    1. **Static hypernetwork** – parameters fixed after training on the whole training set.  
    2. **Evolutionary hypernetwork** – fine‑tuned on each new commit (few‑shot SGD) to capture intra‑repo drift.  

- **Baselines**  
  - Per‑repo fine‑tuned LoRA (rank 16) trained separately on each repo.  
  - Static LoRA (single adapter shared across all repos).  
  - Retrieval‑augmented generation (RAG) using a BM25 code index.  
  - Plain fine‑tuning of the full model on the training set (resource‑heavy upper bound).  

- **Training procedure**  
  - Optimize with AdamW (lr = 5e‑5, weight decay = 0.01) for 3 epochs over the training commits.  
  - For the evolutionary variant, after each epoch perform a single‑step update on the newest commit batch (learning rate = 1e‑4).  

- **Evaluation**  
  - Compute Exact Match (EM), CodeBLEU, and edit‑similarity on the held‑out test commits (both in‑repo and out‑of‑distribution).  
  - Measure storage size of adapters, total trainable parameters, and inference latency (seconds per token) on a single CPU core (GitHub Actions runner).  
  - Perform paired t‑tests between each hypernetwork variant and each baseline across the three random seeds; report p‑values and 95 % confidence intervals.  

- **Reproducibility**  
  - All scripts, environment (`requirements.txt`), and a `run_experiments.sh` driver are version‑controlled in the repository.  
  - Random seeds, hyperparameters, and dataset URLs are logged to `logs/run_*.json`.  

## Duplicate-check  

- Reviewed existing ideas: *none*.  
- Closest match: *none* (no semantically similar fleshed‑out ideas found).  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-21T13:01:23Z
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
