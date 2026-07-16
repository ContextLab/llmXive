---
action_items:
- id: 1bed4500baec
  severity: writing
  text: The paper presents a compelling hypothesis that image-conditioned prompt likelihood
    serves as an effective zero-shot reward signal. However, the experimental design
    contains specific gaps that prevent the reported results from definitively establishing
    the claimed causal mechanisms, particularly regarding the stability of the gains
    and the isolation of the "alignment" effect. First, the main results in Tables
    2 and 3 are presented as single-point estimates (e.g., Self-Method achieving 89.5
    on Ge
artifact_hash: 7fff84212e932b4d992732fd5a0527c97171ad9bb6da5fea5186ea23bf6fee03
artifact_path: projects/PROJ-1068-read-it-back-pretrained-mllms-are-zero-s/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-16T04:00:57.520680Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling hypothesis that image-conditioned prompt likelihood serves as an effective zero-shot reward signal. However, the experimental design contains specific gaps that prevent the reported results from definitively establishing the claimed causal mechanisms, particularly regarding the stability of the gains and the isolation of the "alignment" effect.

First, the main results in Tables 2 and 3 are presented as single-point estimates (e.g., Self-Method achieving 89.5 on GenEval) without any indication of variance. Reinforcement learning training is notoriously sensitive to random seeds, hyperparameter initialization, and stochastic sampling. A single run cannot distinguish a genuine improvement from a lucky seed or a specific trajectory. The absence of standard deviations, confidence intervals, or a stated number of seeds (n) makes it impossible to assess whether the reported margins (e.g., +1.2 over the best external MLLM) are statistically significant or within the noise floor of the training process. To support the claim of "consistent improvement," the authors must report results averaged over multiple independent training runs (at least 3-5 seeds).

Second, the comparison between Self-Method and external reward models (Table 2) conflates the quality of the reward signal with the computational cost and inference architecture. Self-Method leverages the policy's own understanding branch, incurring zero additional inference overhead, whereas external MLLMs (like Qwen3-VL-30B) require separate, expensive forward passes. The paper attributes the superior performance of Self-Method to "reward-policy alignment," but it does not rule out the alternative explanation that the external models were simply under-utilized or that the comparison is unfair due to the massive difference in inference cost. To isolate the "alignment" hypothesis, the authors should either report a compute-matched baseline (e.g., using a smaller external model that matches the inference cost of the self-reward) or explicitly demonstrate that the performance gap persists even when the external model is given equal computational resources or tuning effort.

Finally, the ablation study in Section 4.2 (Table 4) compares the proposed reward against scalar scoring and VQA-Score but does not fully control for the optimization algorithm and hyperparameters. The paper states that AWM was chosen because it performed best with Self-Method, but it does not show whether the same hyperparameters (learning rate, steps, group size) would yield similar gains if applied to a different reward function. It is plausible that the observed gains are partly due to the specific hyperparameter configuration being well-suited to the prompt-likelihood reward's gradient properties, rather than the reward function itself being inherently superior. A more rigorous ablation would fix the hyperparameters across all reward types or report a grid search for each to ensure the comparison is fair.

Addressing these points—specifically by adding seed variance and controlling for compute/hyperparameter confounds—would significantly strengthen the evidentiary support for the paper's central claims.
