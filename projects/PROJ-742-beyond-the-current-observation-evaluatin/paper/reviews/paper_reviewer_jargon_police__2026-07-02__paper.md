---
action_items:
- id: 443e4a847833
  severity: writing
  text: The manuscript relies heavily on domain-specific terminology that creates
    unnecessary barriers for non-specialist readers, particularly those in general
    AI or cognitive science. In Section 3.1 (Problem Formulation), the authors introduce
    POMDPs (Partially Observable Markov Decision Processes) without defining the acronym.
    While standard in reinforcement learning, this is a critical concept for the paper's
    premise and should be spelled out and briefly explained for a general audience.
    Similarly,
artifact_hash: 2dace62b4db749210548d655003e141d33d2469d6916df6eba8fda5f05abc5c8
artifact_path: projects/PROJ-742-beyond-the-current-observation-evaluatin/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T14:46:53.309200Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific terminology that creates unnecessary barriers for non-specialist readers, particularly those in general AI or cognitive science.

In **Section 3.1 (Problem Formulation)**, the authors introduce **POMDPs** (Partially Observable Markov Decision Processes) without defining the acronym. While standard in reinforcement learning, this is a critical concept for the paper's premise and should be spelled out and briefly explained for a general audience. Similarly, the term **egocentric** (Section 3.2) is used to describe the 3D Maze view; replacing this with "first-person" or "agent-centric" would be more intuitive.

**Section 5 (Training Strategy)** and the **Appendix** frequently use the term **rollouts** to describe the data used for fine-tuning. This is RL jargon that obscures the meaning; "simulated game histories" or "complete game trajectories" would be more accessible. Additionally, the metric **Traj-Match** (Section 4.2, Appendix) is introduced without a clear definition of what constitutes a "match" between a model's output and the ground truth, leaving the reader to guess the calculation method.

Finally, the term **ablation** is used repeatedly in section headers (e.g., "Visual-pattern ablation," "Ask-output ablation"). While common in ML, "removal study" or "component analysis" would better convey the intent to a broader readership. The **Memory Gap** metric is well-explained, but its reliance on the undefined "oracle" concept in Equation 2 could be slightly clarified by explicitly stating that the oracle represents a model with perfect memory injection.

These changes would significantly improve the paper's readability without sacrificing technical precision.
