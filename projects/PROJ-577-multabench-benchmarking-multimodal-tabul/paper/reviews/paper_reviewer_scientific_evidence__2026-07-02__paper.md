---
action_items:
- id: 09b36a5a74ee
  severity: science
  text: The curation pipeline entangles 'Task-awareness' with the specific LoRA finetuning
    algorithm. Datasets are selected because TAR works, creating a circular bias.
    Clarify if this property is intrinsic to the data or an artifact of the specific
    encoder/finetuning strategy used for selection.
- id: 7fa20ca013ad
  severity: science
  text: Discretizing regression targets into 20 bins for TAR finetuning may distort
    the signal. Provide evidence that this preserves fine-grained information or compare
    against direct regression finetuning to rule out this confounding variable.
- id: 953239e01227
  severity: science
  text: Non-curation models (e.g., TabICLv2, ConTextTab) show significantly lower
    win rates (55-76%) than curation models. Discuss whether the benchmark is overfit
    to the specific inductive biases of the curation models and if generalization
    claims hold for other architectures.
artifact_hash: 28e097e31933ecce294eb34fd92a9e53c4dcbbab117fcc0a77af75a314777084
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:48:49.573278Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling argument for the necessity of Target-Aware Representations (TAR) in Multimodal Tabular Learning (MMTL) and introduces MulTaBench, a curated benchmark of 40 datasets. The experimental design is generally robust, utilizing 5 random seeds, multiple tabular learners, and ablation studies on encoder scale and dimensionality. The evidence supporting the central claim—that frozen embeddings lose task-specific signal—is strong, with consistent performance gains observed across the majority of models and datasets.

However, the scientific validity of the benchmark's curation criteria warrants closer scrutiny. The definition of "Task-awareness" is operationally defined by the success of a specific algorithmic intervention (LoRA finetuning of the last 3 layers). This creates a potential circularity: datasets are selected *because* they respond to this specific intervention, which inherently biases the benchmark toward models that utilize similar finetuning strategies. While the authors acknowledge this entanglement in the Discussion, the paper does not sufficiently rule out the possibility that the observed "Task-awareness" is an artifact of the specific encoder architecture (DINO/e5) or the finetuning hyperparameters rather than an intrinsic property of the data distribution.

Furthermore, the methodological choice to discretize regression targets into 20 bins for the TAR finetuning step (Appendix, Section "Regression") introduces a potential confound. There is no analysis provided to demonstrate that this discretization preserves the fine-grained signal necessary for the downstream regression task, nor is there a comparison against direct regression finetuning. If the discretization smooths out the very noise or fine-grained details that TAR is supposed to recover, the validity of the "Task-awareness" claim for regression tasks is weakened.

Finally, while the paper claims generalization across learners, the win rates for non-curation models (e.g., TabICLv2 at 55%, ConTextTab at 73%) are notably lower than for the curation models (80-93%). This suggests the benchmark may be somewhat specialized to the inductive biases of the models used during curation. The authors should provide a more nuanced discussion on the extent to which the benchmark results are transferable to architectures with fundamentally different learning dynamics.
