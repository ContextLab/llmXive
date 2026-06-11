---
action_items:
- id: bffc1f26ab1c
  severity: writing
  text: Define all acronyms (MoE, RL, KL, PPO, GRPO, RLVR, SVD, PiSSA, MiLoRA, OLoRA,
    DAPO, TIM, MinT, ALFWorld, AIME) at first occurrence throughout the manuscript.
- id: efe02f86fcce
  severity: writing
  text: Ensure "TIM" (Training-Inference Mismatch) is defined in the text before its
    use in the Figure 3.2 caption.
- id: 28f75b107846
  severity: writing
  text: Simplify or explain technical phrases like "KL leash", "trajectory distribution",
    and "expert routing" for non-specialist readers.
- id: c5e691e4c9b2
  severity: writing
  text: Briefly describe benchmarks (DishNameBenchmark, ALFWorld, AIME24) upon first
    mention to clarify their purpose.
artifact_hash: 98f7fcdee505c1b0d734c7251a396631b218366acf62d66b7a26c51efa8d758b
artifact_path: projects/PROJ-655-https-arxiv-org-abs-2606-02437/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T22:06:02.046764Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript introduces a compelling three-axis framework for PEFT scaling but relies heavily on undefined acronyms and specialized terminology that excludes non-specialist readers. This density of jargon obscures the core contributions for those outside the specific RLHF niche.

1.  **Undefined Acronyms**: Numerous acronyms appear before definition. "MoE" (Mixture-of-Experts) is used in Section 3.1.1 without expansion. "RL" (Reinforcement Learning) appears throughout Section 3 without definition. "KL" (Kullback-Leibler) divergence is referenced in Section 4.1.1 without explanation. "PPO", "GRPO", "RLVR", "SVD", "PiSSA", "MiLoRA", "OLoRA", "DAPO", "TIM", "MinT", "ALFWorld", and "AIME" are similarly introduced without context. Define all acronyms at first occurrence.
2.  **Premature Acronym Usage**: "TIM" appears in Figure 3.2 caption before being defined in Section 3.2.4. Ensure definitions precede usage.
3.  **Technical Density**: Phrases like "KL leash", "trajectory distribution", "expert routing", and "on-policy" assume deep RL knowledge. Replace with plainer alternatives (e.g., "policy constraint", "sequence probability", "expert selection") or add brief parenthetical explanations.
4.  **Benchmark Names**: Benchmarks like "DishNameBenchmark", "ALFWorld", and "AIME24" are used without description. Briefly state their purpose (e.g., "math reasoning benchmark").
5.  **Model Architectures**: Terms like "MLA", "DSA", and "MTP" in Section 3.2.3 are specific to certain model families and need definition for general understanding.
6.  **Section 5 Terminology**: "Context Learning" and "Context Distillation" are introduced in Section 5.1.2 without distinguishing them from standard in-context learning. Clarify the distinction explicitly.

These changes will significantly improve accessibility without diluting technical rigor. A glossary appendix is also recommended for the many custom method names (e.g., OLoRA-tail, $\delta$-mem).
