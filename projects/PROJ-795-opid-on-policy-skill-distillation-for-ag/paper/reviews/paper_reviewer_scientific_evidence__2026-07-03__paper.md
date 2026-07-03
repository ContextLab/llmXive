---
action_items:
- id: 7cfdff34f16f
  severity: writing
  text: The paper presents a compelling method (OPID) for enhancing agentic RL via
    on-policy skill distillation. However, the evidentiary strength of the central
    claims is currently undermined by a lack of statistical rigor in the experimental
    design. The primary concern is the absence of variance reporting. Table 1 presents
    headline performance numbers (e.g., 84.3% vs 75.0% on ALFWorld) derived from what
    appears to be single training runs. In reinforcement learning, performance is
    highly sensitive to r
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T20:05:14.742568Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method (OPID) for enhancing agentic RL via on-policy skill distillation. However, the evidentiary strength of the central claims is currently undermined by a lack of statistical rigor in the experimental design.

The primary concern is the absence of variance reporting. Table 1 presents headline performance numbers (e.g., 84.3% vs 75.0% on ALFWorld) derived from what appears to be single training runs. In reinforcement learning, performance is highly sensitive to random seeds, hyperparameter initialization, and rollout stochasticity. A single-point improvement of ~9% is well within the range of variance observed in standard RL baselines. Without reporting results across multiple seeds (e.g., 3-5) with mean and standard deviation, the reader cannot determine if the reported gains are a robust effect of the method or a lucky seed. This is a critical gap for a paper claiming "consistent improvements."

Secondly, the ablation studies do not fully isolate the proposed mechanisms. The "w/o Routing" ablation (Table 4) removes the critical-first logic but leaves the skill extraction and injection pipeline intact. It is unclear if the performance drop is due to the loss of the routing logic or simply the loss of the specific set of "critical" steps identified by the analyzer. A more rigorous control would inject step-level skills uniformly or randomly to distinguish the value of *routing* from the value of *having* step-level skills.

Finally, the reliance on an external LLM analyzer (GLM-5.2) introduces a potential confound. The paper attributes success to "on-policy" skills, but the analyzer is a separate, potentially stronger model. It is possible the improvement stems from the analyzer's external knowledge or superior reasoning rather than the distillation of the policy's own trajectory. A negative control using a non-intelligent or random text generator as the analyzer would help confirm that the *content* of the extracted skills is the driver, not just the presence of an auxiliary context.

Addressing these design gaps—specifically by adding seed variation and tighter ablation controls—is necessary to substantiate the claim that OPID provides a stable, generalizable improvement over outcome-only RL.
