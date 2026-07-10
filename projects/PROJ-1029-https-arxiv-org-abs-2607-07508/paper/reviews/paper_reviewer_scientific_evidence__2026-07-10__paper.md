---
action_items:
- id: 5b9f98524281
  severity: writing
  text: The paper presents a compelling method for asynchronous RL, but the experimental
    design contains specific gaps that prevent the evidence from fully supporting
    the central claims regarding the efficacy of the "single-rollout" strategy versus
    group-wise sampling. First, the primary results in Tables 1 and 2 report single-point
    accuracy numbers (e.g., 97.3% vs 94.2% on AIME2025) without any indication of
    variance, standard deviation, or the number of random seeds used. Reinforcement
    learning traini
artifact_hash: 074dab51b251c3b23d6db9c80303fd38538e422225236058b520e4d397713f46
artifact_path: projects/PROJ-1029-https-arxiv-org-abs-2607-07508/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-10T04:20:46.088337Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for asynchronous RL, but the experimental design contains specific gaps that prevent the evidence from fully supporting the central claims regarding the efficacy of the "single-rollout" strategy versus group-wise sampling.

First, the primary results in Tables 1 and 2 report single-point accuracy numbers (e.g., 97.3% vs 94.2% on AIME2025) without any indication of variance, standard deviation, or the number of random seeds used. Reinforcement learning training is highly stochastic; a 3.1% absolute gain on a benchmark could easily be the result of a lucky seed or sampling noise. Without reporting results across multiple seeds (e.g., 3-5) with mean ± standard deviation, the reader cannot distinguish a robust algorithmic improvement from a statistical fluke. The claim that the method "consistently outperforms" is not supported by the lack of variance reporting.

Second, the ablation studies fail to isolate the specific contribution of the "single-rollout" mechanism from the introduction of a value model. The proposed method (SAO) uses single-rollout sampling *and* a trained value model, whereas the baseline (GRPO) uses group-wise sampling *without* a value model. The paper attributes the performance gain to the single-rollout design, but it is equally plausible that the gain comes from the presence of a value model (which reduces variance) rather than the removal of group-wise sampling. The ablation in Table 3 compares "Single-step-update" and "Full-Parameter" variants of SAO, but it does not compare a single-rollout method *without* a value model (e.g., using a running-mean baseline) against a group-wise method *with* a value model. To claim the single-rollout strategy is the key innovation, the authors must demonstrate that single-rollout with a value model beats group-wise with a value model, or that single-rollout with a simple baseline beats group-wise without one.

Third, there is a potential confound in the hyperparameter settings. The paper specifies a double-sided clipping range of $[0.3, 5.0]$ for SAO. Standard PPO/GRPO implementations typically use symmetric bounds like $[0.8, 1.2]$ or $[0.2, 1.2]$. The upper bound of 5.0 is exceptionally permissive, allowing for massive policy updates that standard baselines would clip. It is unclear if the performance gain is due to the asynchronous design or simply the ability to take much larger, less constrained steps. A fair comparison requires tuning the GRPO baseline with the same aggressive clipping bounds to ensure the comparison isolates the rollout strategy rather than the clipping hyperparameters.

Addressing these points—reporting multi-seed variance, adding an ablation that isolates the value model's contribution, and controlling for clipping asymmetry—is necessary to substantiate the claim that the single-rollout asynchronous design is the primary driver of the observed improvements.
