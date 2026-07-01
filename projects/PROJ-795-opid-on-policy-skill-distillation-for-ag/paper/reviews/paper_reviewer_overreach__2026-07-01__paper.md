---
action_items:
- id: 8ed28cfcb68d
  severity: science
  text: The claim that OPID 'internalizes skills' (Sec 4.2) overstates evidence. The
    +37.8pt gain vs Skill-GRPO without skill input conflates removing inference prompts
    with removing training distillation. Clarify if baselines were re-trained; otherwise,
    'internalization' is unsupported.
- id: 2475d6dfcdd2
  severity: science
  text: Proposition 3 (App A.3) claims routing error is bounded by detector error,
    yet no empirical detector accuracy is reported. Without measuring critical step
    identification precision, the theoretical bound is abstract and does not justify
    routing's empirical contribution.
- id: da95cd3e1e94
  severity: writing
  text: The claim of 'best average' on Search-based QA (Sec 4.2) is unsupported by
    Table 1, which omits scores for baselines like SDAR/RLSD in those columns. Explicitly
    compare against all listed baselines to validate the 'best' claim.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T00:03:32.433006Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims regarding the mechanism and generalization of OPID that extend beyond the provided empirical evidence.

First, the central claim in Section 4.2 that OPID "internalizes skills" and outperforms Skill-GRPO by +37.8 points on Qwen3-1.7B "without any skill input" is potentially misleading. The text states that when "validation-time skills are removed, Skill-GRPO underperforms ordinary GRPO." This implies the baseline comparison is between a model trained with distillation but tested without prompts (Skill-GRPO) versus a model trained *without* distillation (GRPO). If the "Skill-GRPO" baseline was not re-trained to remove the distillation objective, the comparison is invalid for proving "internalization." The paper must explicitly state whether the baselines were re-trained ablation studies or if the comparison is merely between inference-time configurations. If the latter, the claim that the *policy* has internalized the skill is an over-interpretation of the data.

Second, the theoretical analysis in Appendix A.3 (Proposition 3) asserts that the routing error is bounded by the detector error probability. However, the paper never reports the accuracy of the "criticality detector" (the LLM analyzer identifying critical timesteps). Without an empirical measurement of the detector error rate, the theoretical guarantee remains abstract and does not substantiate the claim that the routing mechanism is the primary driver of the observed performance gains. The authors should provide a diagnostic table showing the precision/recall of the critical step identification.

Finally, the claim that OPID achieves the "best average" on Search-based QA (Section 4.2) is not fully supported by Table 1. While OPID beats GRPO, the table does not clearly display the scores for all listed baselines (e.g., SDAR, RLSD) in the Search-based QA columns, making the "best" claim unverifiable from the provided data. The authors must ensure all comparative claims are backed by complete data in the tables.
