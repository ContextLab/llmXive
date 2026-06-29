---
action_items:
- id: 82bcfa74dfe1
  severity: science
  text: Report statistical significance (p-values or confidence intervals) for the
    main performance gains, particularly the 8B vs 32B comparison, as the reported
    standard deviations (tab_main_p1_std.tex) suggest the margins are within noise.
- id: bc84f4131e61
  severity: science
  text: Clarify the total sample size (number of questions/steps) used to generate
    the diagnostic curves in Figure 3 (fig3.tex) to ensure the trend analysis is robust.
- id: ef3beb77b7fe
  severity: science
  text: Provide a more detailed compute budget comparison (FLOPs or wall-clock time)
    between AXPO's 25% resampling budget and the 2x rollout baseline in Table 2 to
    validate the efficiency claim.
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:47:14.372809Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper proposes AXPO to address the "Thinking-Acting Gap" in multimodal agentic reasoning. While the methodological design is sound and the ablation study (Table 1, `tables/tab_ablation.tex`) effectively isolates components, the scientific evidence supporting the magnitude of the reported gains requires strengthening.

First, the statistical significance of the main results is not rigorously established. Table 3 (`tables/tab_main_p1_std.tex`) reports standard deviations across four independent evaluation rollouts. At the 8B scale, the Pass@1 gain over SFT+GRPO is +1.8 pp with a column-averaged std of 1.2 pp. This represents a ~1.5 sigma effect, which is not statistically significant at p<0.05 without a paired test. More critically, the claim that 8B AXPO "surpasses" the 32B Base on Pass@4 (75.8 vs 75.1, a 0.7 pp difference) is within the reported noise margin (std ~1.2 pp). Please report p-values or bootstrap confidence intervals for these key comparisons to avoid overclaiming.

Second, the diagnostic analysis in Section 2.2 (`text/2_method.tex`, Figure 3) relies on trends over RL steps. The text mentions "8 rollouts/question" but does not specify the total number of questions or training steps aggregated to produce the curves in `figures/fig3_analysis_a.pdf` and `b.pdf`. A larger sample size would increase confidence that the observed "all-wrong" rates are stable and not artifacts of specific batch compositions.

Third, while Table 2 (`tables/tab_comparison.tex`) compares AXPO against a 2x rollout budget, the efficiency claim ("25% extra resampling budget... delivers +1.1 pp over +100% extra rollout budget") assumes comparable computational cost per rollout. Resampling fixed prefixes may incur different overheads than standard rollouts. Explicitly reporting FLOPs or wall-clock time would solidify the evidence that the gain comes from "where" compute is spent rather than total volume.

Finally, the generalization claim regarding unseen tools (Table 5, `tables/tab_image_search.tex`) relies on a GPT-5.4 proxy for the image-search tool. While acknowledged as an approximation, this limits the evidence for true generalization to new tool interfaces. A real API test, even on a subset, would strengthen this claim.
