---
action_items:
- id: 7f1d36835d26
  severity: writing
  text: Title and Abstract claim 'Generalization Beyond 128K Context' and 'strong
    performance at 256K/512K'. Table 5 shows a performance drop from 59.56 (64K) to
    52.52 (512K). Temper these claims to reflect extrapolation limits rather than
    robust generalization.
- id: 5c3573ecde91
  severity: writing
  text: Section 5.2 claims 8:2 extraction-to-reasoning ratio is 'optimal'. The margin
    over 6:4 (57.70 vs 57.27) is 0.43 points, likely within evaluation noise. Qualify
    this claim as 'best observed' rather than optimal.
- id: d9a7f561ac35
  severity: writing
  text: Section 6.1 claims generalization to long-video tasks 'without video-specific
    training'. Gains are modest (~3 points). Clarify that this is transfer capability,
    not optimized performance, to avoid overreach on video understanding claims.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T13:22:27.838596Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a solid empirical study, but several claims in the Abstract and main text slightly overreach the supported data, particularly regarding context length extrapolation and data mixture optimization.

First, the title "Generalization Beyond 128K Context" and the Abstract claim of "strong performance at 256K/512K contexts" are optimistic. Table 5 shows a notable performance drop from 59.56 (64K) to 52.52 (512K). While the model outperforms the baseline significantly, the degradation suggests limits to the extrapolation. Describing this as "strong performance" without qualifying the drop overstates the robustness of the 512K capability. The title implies the method *enables* beyond-128K usage, whereas the evidence shows it *allows* extrapolation with diminishing returns.

Second, Section 5.2 asserts that an 8:2 extraction-to-reasoning ratio is "optimal." Table 3 shows the 8:2 ratio achieves 57.70, while the 6:4 ratio achieves 57.27. This 0.43-point difference is marginal and likely within the variance of LLM-based judging. Labeling 8:2 as "optimal" implies a level of certainty not supported by the statistical margin. It should be framed as "best observed" or "preferred" rather than optimal.

Third, Section 6.1 claims generalization to long-video tasks "without video-specific training" (Figure 8). While consistent gains are observed (e.g., +2.68 on Video-MME), the absolute gains are modest compared to the document task improvements (+7.1%). Framing this as effective generalization might overstate the method's transferability to video domains, where temporal reasoning is distinct from document retrieval.

Finally, the Appendix presents a diagnostic transfer to Qwen3-VL-8B, which is already a 256K model. While this shows recipe transferability, it does not directly validate the "Beyond 128K" claim for models trained only up to 128K.

To address these overreach concerns, I recommend tempering the language in the Abstract and Title regarding 512K performance, qualifying the "optimal" mixture claim, and clarifying the scope of video generalization.
