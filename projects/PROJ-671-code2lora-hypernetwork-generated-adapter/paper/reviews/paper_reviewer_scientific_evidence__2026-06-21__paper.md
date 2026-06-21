---
action_items:
- id: 415e3f821a45
  severity: science
  text: Report variance (e.g., standard deviation or confidence intervals) for all
    primary metrics (EM, EditSim, CodeBLEU) across multiple random seeds or data splits
    to assess statistical significance of reported gains.
- id: 1bf20e76927a
  severity: science
  text: "Include statistical hypothesis testing (e.g., paired t\u2011tests or bootstrap)\
    \ comparing Code2LoRA variants against each baseline, and report p\u2011values\
    \ to guard against chance improvements."
- id: 7e6f9760492c
  severity: science
  text: Clarify the random seed handling and whether experiments were repeated; if
    only a single run was performed, add at least three runs with different seeds
    for each method.
- id: a2710eca0411
  severity: science
  text: Provide a more detailed ablation of key hyperparameters (e.g., LoRA rank,
    GRU hidden size, number of training epochs) to demonstrate robustness of the central
    claims to these design choices.
- id: 438a13540cb2
  severity: science
  text: "Discuss potential overfitting to the specific benchmark (RepoPEFTBench) and\
    \ evaluate on an additional, independently sourced code\u2011completion benchmark\
    \ to strengthen external validity."
- id: c574f1656d5c
  severity: writing
  text: "Report the total number of trainable parameters for each baseline (including\
    \ per\u2011repo LoRA) and the memory/computation overhead during inference to\
    \ contextualize the claimed efficiency gains."
artifact_hash: fad4da344b5e72bb204a08d5e9a960cbc3b14e42d22c2e81bf4f3bf3224fac8e
artifact_path: projects/PROJ-671-code2lora-hypernetwork-generated-adapter/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-21T12:46:26.845148Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive experimental evaluation of Code2LoRA, a hypernetwork that generates repository‑specific LoRA adapters for code language models. The authors introduce a sizable benchmark (RepoPEFTBench) with over 400 Python repositories, both static and evolution tracks, and report exact‑match, edit‑similarity, and CodeBLEU scores for many baselines (pretrained, RAG, DRC, full fine‑tuning, single‑LoRA, per‑repo LoRA, Text2LoRA). The reported improvements (e.g., +15 pp EM over the strongest baseline in the static track, +5 pp EM over per‑repo LoRA in the evolution track) are substantial.

**Strengths of the evidence**

- **Sample size and diversity**: The benchmark includes 409 training repos and a held‑out cross‑repo test set of 52 repos, plus an out‑of‑distribution set of 92 repos. The evolution track adds >45 k commits, providing a realistic longitudinal evaluation.
- **Controls and baselines**: A wide range of strong baselines is included, covering context‑injection (RAG, DRC), full fine‑tuning, and parameter‑efficient adapters (single‑LoRA, per‑repo LoRA, Text2LoRA). This allows a clear attribution of gains to the hypernetwork‑generated adapters.
- **Ablations**: The paper contains several ablations (e.g., repository‑count scaling, GRU recurrence, DRC coverage) that help isolate the contribution of each component.
- **Replication details**: Training hyperparameters, compute resources (single H100 GPU), and dataset construction steps are described, and code/data are promised to be released.

**Weaknesses and risks**

1. **Absence of statistical significance reporting** – All tables present point estimates only. No standard deviations, confidence intervals, or p‑values are provided, making it impossible to judge whether the observed differences are robust to random variation (e.g., different seeds, data splits).

2. **Single‑run experiments** – The manuscript does not state that each configuration was run multiple times. Without repeated runs, the risk of over‑interpreting a lucky seed or a particular data split is high.

3. **Limited evaluation metrics** – The primary metrics are surface‑level (Exact Match, Edit Similarity, CodeBLEU). While appropriate for assertion‑completion, they do not capture functional correctness or downstream impact on real‑world coding tasks.

4. **Potential overfitting to the benchmark** – All experiments are confined to the newly introduced RepoPEFTBench. Although an OOD split is provided, it still derives from the same collection pipeline (GitHub Python repos, similar task format). External validation on a distinct code‑completion benchmark would strengthen the claim of generality.

5. **Parameter‑efficiency claims lack quantitative comparison** – The paper reports total hypernetwork parameters (≈720 M) but does not consistently compare inference latency, memory footprint, or storage overhead across all baselines (e.g., per‑repo LoRA vs. Code2LoRA). Table \ref{tab:efficiency} gives a high‑level view but lacks concrete numbers (e.g., MB per repo, latency in ms).

6. **Hyperparameter sensitivity not fully explored** – While some ablations are shown, key design choices (LoRA rank = 16, GRU hidden size = 2048, number of training epochs = 3) are not varied. Demonstrating that the main results hold across reasonable ranges would reduce the chance of “hyperparameter tuning” bias.

**Overall assessment**

The experimental design is solid and the dataset is large enough to support the central claims. However, the lack of statistical rigor (no variance reporting, no repeated runs, no significance testing) limits confidence in the magnitude of the reported improvements. Addressing these issues would make the evidence substantially more robust.

**Recommendation:** Minor revision – the authors should augment the manuscript with statistical analyses, multiple‑seed experiments, and clearer efficiency comparisons, and optionally add an external benchmark to confirm generalization.
