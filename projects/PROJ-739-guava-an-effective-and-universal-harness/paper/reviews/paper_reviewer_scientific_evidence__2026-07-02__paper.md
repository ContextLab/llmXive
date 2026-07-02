---
action_items:
- id: 1970a2efd014
  severity: science
  text: The claim of 'fewer than 2K trajectories' (Abstract, Sec 1) lacks statistical
    power analysis. With N=15 episodes per task (Table 1), the confidence intervals
    for success rates (e.g., 6.7% vs 53.3%) are extremely wide. Report 95% CIs or
    standard errors for all success rates to validate the significance of the reported
    gains.
- id: 165e82e68e09
  severity: science
  text: The RL ablation (Fig 4, Sec 4) compares SFT vs. RL on only two tasks ('shell
    game', 'place all red objects'). This sample size is insufficient to support the
    broad claim that RL 'substantially improves long-horizon reasoning' generally.
    Include results on at least 2-3 additional long-horizon tasks to rule out task-specific
    overfitting.
- id: 7d8a142bc984
  severity: science
  text: The harness ablation study (Fig 2) relies on a single frontier model (GPT-5.4).
    To support the claim that the design principles are 'universal' (Abstract), the
    ablation must be replicated on at least one other distinct model architecture
    (e.g., a different parameter scale or family) to demonstrate robustness against
    model-specific biases.
- id: c77f90b3a78c
  severity: science
  text: The Sim-to-Real transfer claim (Sec 4, Finding 2) is based on 10 episodes
    per task. Given the stochastic nature of real-world robotics, this sample size
    is too small to distinguish between genuine generalization and random variance.
    Increase real-world evaluation to at least 30 episodes per task or provide a statistical
    test comparing simulation vs. real-world performance distributions.
artifact_hash: 305fa4e0caf5509b3ff951ed539855921f525d3dfdda7d54d245e51eb00f86f3
artifact_path: projects/PROJ-739-guava-an-effective-and-universal-harness/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T04:37:11.011565Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling framework, but the scientific evidence supporting the central claims of universality and robustness is currently underpowered. While the reported success rates are promising, the sample sizes (N=15 for simulation, N=10 for real-world) are insufficient to draw statistically significant conclusions, particularly for the lower-performing tasks where confidence intervals likely overlap.

Specifically, the claim that the harness design is "universal" (Abstract) is tested only on GPT-5.4 in the ablation study (Fig 2). Without replicating these ablations on a second, distinct model family, it is unclear if the observed benefits are due to the harness or specific capabilities of the GPT-5.4 model. Similarly, the assertion that RL post-training "substantially improves" long-horizon reasoning (Finding 3) is based on only two tasks. This small N makes the result vulnerable to task-specific idiosyncrasies rather than a generalizable improvement in reasoning.

Furthermore, the real-world evaluation (N=10) is statistically weak for robotics benchmarks where variance is high. The difference between 60% and 40% success rates, for instance, is not statistically distinguishable with such a small sample. The authors should report confidence intervals (e.g., Wilson score intervals) for all success rates and increase the number of real-world trials to ensure the reported "strong generalization" is not a statistical artifact. Finally, the "fewer than 2K trajectories" claim (Abstract) should be contextualized with a power analysis or a discussion on the minimum sample size required to detect the observed effect sizes.
