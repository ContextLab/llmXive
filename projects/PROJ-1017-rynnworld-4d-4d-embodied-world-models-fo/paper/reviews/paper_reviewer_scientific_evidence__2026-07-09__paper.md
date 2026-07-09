---
action_items:
- id: cae39fd05d1b
  severity: science
  text: "The paper presents a compelling architecture for 4D world modeling, but the\
    \ experimental design contains several gaps that prevent the results from definitively\
    \ supporting the strength of the claims made. First, the ablation studies in Table\
    \ 2 (World Modeling) and Table 3 (Policy Learning) rely on single-point estimates\
    \ without reporting variance. For instance, the improvement in geometric accuracy\
    \ (\u03B41) when adding Modality Adaptation is 0.131 (0.610 vs 0.479). In generative\
    \ modeling, where resu"
artifact_hash: 17fb6218664f43578c4bdeeb1bf60943385a2c06b8b83361a91553cd1f9ccab8
artifact_path: projects/PROJ-1017-rynnworld-4d-4d-embodied-world-models-fo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T04:35:46.920381Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The paper presents a compelling architecture for 4D world modeling, but the experimental design contains several gaps that prevent the results from definitively supporting the strength of the claims made.

First, the ablation studies in Table 2 (World Modeling) and Table 3 (Policy Learning) rely on single-point estimates without reporting variance. For instance, the improvement in geometric accuracy (δ1) when adding Modality Adaptation is 0.131 (0.610 vs 0.479). In generative modeling, where results can fluctuate significantly based on random seeds and initialization, a single-run comparison is insufficient to rule out luck. The authors must report mean and standard deviation across at least 3-5 independent training runs for all ablation variants to demonstrate that the observed gains are stable and not artifacts of a specific random seed.

Second, the comparison against foundation models like π0.5 in Table 3 raises concerns about baseline fairness. The baseline achieves 0.00% success on the "Hand-over" task, which is an extreme failure rate for a 35-trial set. This suggests the baseline may have been under-tuned for the specific dexterous hand configuration (WUJI HAND) or the task setup, rather than failing due to the inherent limitations of 2D representations. The paper does not disclose whether the baselines underwent a hyperparameter search comparable to the proposed method. To support the claim that 4D representations are "essential," the authors must ensure baselines are given a fair chance to succeed, either by reporting tuned results or by increasing the trial count to reduce the impact of stochastic failure.

Third, the "w/o 4D Pre-training" ablation claims that the performance collapse is due to data scarcity. However, the text does not explicitly confirm that this ablation was trained for the same number of steps or epochs as the full model. If the ablation was trained for fewer iterations, the poor performance could be attributed to under-training rather than the lack of large-scale data. The authors need to explicitly state that compute budgets were held constant across all ablation experiments.

Finally, the latency breakdown in Table 1 includes "Depth Estimation (DA3)" as a 7.7% overhead. Since the proposed model *generates* depth, the inclusion of an external depth estimator (Depth Anything 3) in the inference pipeline is confusing. If this step is only for ground-truth generation during evaluation, it should not be in the "Inference Latency" table for the policy. If it is part of the deployed system, the authors must clarify why an external estimator is needed when the world model already predicts depth, and ensure the reported 9 Hz frequency accounts for this correctly.
