---
action_items:
- id: 4ae8faca0d36
  severity: science
  text: The claim that 'larger or more capable models sometimes perform worse at timely
    abstention' (Intro) lacks statistical validation. The paper reports point estimates
    (e.g., Qwen3-235B vs smaller variants) but provides no confidence intervals, standard
    errors, or significance tests (e.g., t-tests) to confirm these differences are
    not due to variance, especially given the small sample size of the WebShop abstention
    set (n=500).
- id: b70a17b89a76
  severity: science
  text: The proposed method (Context Evolution) is evaluated on a very small held-out
    set (101 examples) with only 20 training trajectories. The reported jump in AbsRec@1
    from 26.7% to 57.4% (Table 1) risks overfitting to this specific distribution.
    The authors should report performance variance across multiple random seeds or
    provide a cross-validation analysis to demonstrate robustness.
- id: af5df4bf6c61
  severity: science
  text: The dataset construction for 'Request-based Abstention' relies on GPT-5.4-mini
    to rewrite instructions (Section Datasets). The paper claims these are 'semantically
    indistinguishable' (Figure 1) but does not provide a human evaluation of the 'abstain-warranted'
    labels. If the rewriting model introduces subtle biases or if the 'unsolvable'
    nature is ambiguous, the ground truth labels may be noisy, invalidating the AbsRec
    metrics.
artifact_hash: 38d0e8e4fb458c680aadb1d4bcdffd2c4f641f3bec33db525a174585bed1f06b
artifact_path: projects/PROJ-808-agentic-abstention-do-agents-know-when-t/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:29:56.363297Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive empirical study of "Agentic Abstention" across three distinct environments (Web, Terminal, QA) with a total sample size exceeding 28,000 instances. The scale of the evaluation, particularly the 27,073 samples from AbstentionBench, provides a strong foundation for the general claims regarding the difficulty of abstention. The definition of metrics (AbsRec@K) is mathematically rigorous and well-suited to the sequential nature of the problem.

However, the scientific evidence supporting the specific comparative claims regarding model scaling and the efficacy of the proposed \method is weakened by a lack of statistical rigor. In the "Results" section, the authors claim that "larger or more capable models sometimes perform worse at timely abstention." While the point estimates in the text and tables (e.g., Qwen3-235B vs. smaller variants) suggest this trend, the paper does not report confidence intervals, standard deviations, or p-values for these comparisons. Given the stochastic nature of LLM inference and the relatively small sample size of the WebShop abstention subset (n=500), it is impossible to determine if these differences are statistically significant or merely noise.

Furthermore, the evaluation of the proposed \method (Context Evolution) relies on a very small training set (20 trajectories) and a held-out test set of 101 examples. The dramatic improvement reported (e.g., AbsRec@1 rising from 26.7% to 57.4% for Llama-3.3-70B) is compelling but risks overfitting to the specific 20 examples used for playbook generation. The authors should demonstrate that these gains are robust by reporting results across multiple random seeds for the 20-example selection or by performing a cross-validation analysis. Without this, the claim that the method "distills reusable stopping rules" is not fully supported by the evidence provided.

Finally, the ground truth for the "Request-based Abstention" tasks in WebShop and Terminal-Bench is generated via an LLM (GPT-5.4-mini) rewriting process. While the authors provide t-SNE visualizations to show semantic overlap, they do not provide a human evaluation of the "abstain-warranted" labels. If the rewriting model fails to create truly unresolvable tasks or introduces subtle cues that make the task solvable, the evaluation metrics (AbsRec) would be measuring the agent's ability to detect LLM-generated artifacts rather than genuine infeasibility. A human audit of a subset of these rewritten instructions is necessary to validate the dataset quality.
