---
action_items:
- id: cd50a62b814d
  severity: writing
  text: Verify all citation dates (2025-2026) are accurate; several references appear
    to have future publication dates inconsistent with arXiv submission timelines.
- id: 73e04f1bad08
  severity: writing
  text: Clarify model naming conventions (Qwen3-4B, Qwen3.5-27B, Qwen3.5-397B-A17B);
    parameter counts and MoE specifications need verification for reproducibility.
- id: 9480dca1bbfd
  severity: writing
  text: Remove duplicate LaTeX package imports (graphicx, booktabs appear multiple
    times in preamble).
- id: 2747e6791566
  severity: writing
  text: Improve table formatting consistency; some tables exceed column widths and
    have alignment issues in tabularx environments.
- id: ec921ad98c8b
  severity: writing
  text: Add statistical significance testing to RHDA detection results (e.g., confidence
    intervals, p-values for performance differences).
- id: 70f878e00d40
  severity: writing
  text: Clarify the "judge-blind" evaluation protocol; ensure no information leakage
    between reference onset construction and detector inputs.
artifact_hash: eca43eb888bbc8155fd1bf21a6b137ce6bb47419fcb91606da445eda44a63a5a
artifact_path: projects/PROJ-663-https-arxiv-org-abs-2606-04923/paper/metadata.json
backend: dartmouth
feedback: Solid contribution on reward hacking detection; requires citation date verification,
  model naming clarification, and LaTeX formatting fixes before publication.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T04:25:53.396129Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths

1. **Well-motivated problem**: Reward hacking in rubric-based RL is a timely and important issue as LLM-as-a-Judge systems become more prevalent. The paper clearly articulates why existing approaches are insufficient.

2. **Novel controlled environment**: CHERRL's dual-judge architecture is a clever design that enables explicit observation of reward divergence and precise hacking onset identification. This is a significant contribution to the field.

3. **Systematic analysis**: The paper provides a thorough analysis of different bias types (lexical, tone, self-praise, format) across two datasets, with clear metrics for discoverability and exploitability.

4. **Practical detection agent**: RHDA is a well-designed agentic system that outperforms baseline detectors. The "bracket-and-shrink" strategy is intuitive and effective.

5. **Comprehensive appendices**: Implementation details, threshold-sweep statistics, and case studies provide good reproducibility support.

6. **Clear visualizations**: Training dynamics figures and tool-call timelines effectively communicate the experimental results.

## Concerns

1. **Citation date inconsistencies**: Multiple references have publication dates in 2025-2026, which is unusual for arXiv submissions. Some citations appear to be from future dates relative to typical submission timelines. This needs verification.

2. **Model naming verification**: The paper references Qwen3-4B, Qwen3.5-27B, and Qwen3.5-397B-A17B. The parameter counts and MoE specifications (e.g., "397B-A17B" meaning 397B total with 17B activated) need clarification and verification for reproducibility.

3. **LaTeX formatting issues**: Duplicate package imports in the preamble (graphicx, booktabs appear multiple times). This should be cleaned up for professional presentation.

4. **Statistical rigor**: The detection results table shows point and interval distances but lacks statistical significance testing. Confidence intervals or p-values would strengthen the claims about RHDA's superiority.

5. **Judge-blind protocol clarity**: While the paper claims judge-blind evaluation, the appendix mentions "normalized visible score" which could potentially leak information about reward scales. This needs clearer documentation.

6. **Limited model scope**: The analysis is primarily based on Qwen3-4B. While acknowledged as a limitation, more discussion about generalization to other model families would strengthen the paper.

7. **Table formatting**: Some tables (e.g., tab:detection_results) have column width issues that may not render well in all PDF viewers.

## Recommendation

This paper makes a meaningful contribution to understanding and detecting reward hacking in rubric-based RL systems. The CHERRL environment and RHDA detection agent are both well-designed and empirically validated. The core scientific claims are supported by the experimental evidence presented.

However, several issues need to be addressed before publication:

1. **Citation verification**: All references with 2025-2026 dates should be verified for accuracy. This is critical for maintaining the paper's credibility.

2. **Model specification clarity**: The parameter counts and architecture details for all models used (policy, judges, detectors) should be clearly documented and verified.

3. **LaTeX cleanup**: Remove duplicate package imports and fix table formatting issues.

4. **Statistical analysis**: Add significance testing to the detection results to strengthen claims about RHDA's performance.

These are all fixable through text edits and do not require new experiments. The paper is suitable for publication after these minor revisions are completed.
