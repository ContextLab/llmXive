---
action_items:
- id: d007ce9b9932
  severity: writing
  text: The claim that 'over 70% of localizations would be false positives' (Abstract)
    overgeneralizes. The 73.4% figure (Sec 3.1) applies only to regions found by the
    MindSimulator baseline, not all activation-based methods in the field. Qualify
    this claim to reflect the specific baseline comparison.
- id: b6c77502ff55
  severity: writing
  text: The Abstract claims BrainCause 'successfully recovers known functional localizations.'
    Table 1 shows alignment with broad categories (e.g., 'Faces'), but does not demonstrate
    recovery of specific fine-grained sub-regions (e.g., FFA vs. OFA) with higher
    fidelity than baselines. Temper the claim to 'broad functional regions'.
- id: 781afd352771
  severity: writing
  text: The conclusion states 'without causal validation, a large fraction of localizations
    would be false positives.' This generalizes beyond the study's scope (NSD, 260
    concepts, specific baselines). Restrict the claim to the evaluated methods and
    datasets to avoid overreach regarding the broader literature.
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T16:19:36.512776Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several strong claims regarding the prevalence of false positives in activation-based methods and the superior ability of BrainCause to recover "true" representations. While the internal logic of the BrainCause framework is sound and the comparison with MindSimulator is well-executed, the manuscript occasionally overreaches in generalizing these findings to the broader field of neuroscience.

Specifically, the Abstract and Introduction state that "over 70% of localizations would be false positives" and that "a large fraction of localizations would be false positives" without causal validation. The data supporting this (Section 3.1, Fig. 3) shows that 73.4% of the regions *discovered by the MindSimulator baseline* fail the causal test. This is a valid finding about the MindSimulator method and the specific 260 concepts tested. However, extrapolating this to imply that 70% of *all* activation-based discoveries in the literature are false positives is an overreach. The MindSimulator baseline may have specific failure modes (e.g., reliance on CLIP retrieval) that do not generalize to all activation-maximization approaches used in the field. The language should be tempered to reflect that this high false-positive rate was observed specifically for the baseline method and concept set evaluated, rather than as a universal statistic for the field.

Additionally, the claim that BrainCause "successfully recovers known functional localizations" (Abstract) is slightly overstated given the evidence. Table 1 shows high alignment for broad categories (e.g., 90% of top voxels for "Faces" fall in face-selective regions). However, this does not necessarily demonstrate the recovery of specific, fine-grained functional maps (e.g., distinguishing FFA from OFA with high precision) better than baselines, but rather that the method finds *some* voxels in the correct general vicinity. The paper would benefit from clarifying that it recovers *broad* functional regions consistent with known anatomy, rather than implying a precise recovery of established fine-grained maps that might be difficult to validate without ground-truth anatomical data.

Finally, the conclusion asserts that the work "reveals that many previously identified representations may be driven by correlated factors." While the paper demonstrates this for the specific concepts and baselines tested, it does not provide a systematic re-analysis of previously published "known" representations (e.g., from the original Kanwisher or Epstein papers) to confirm they are false positives. The claim remains a strong inference based on the current study's limitations rather than a direct refutation of prior literature. Restricting these claims to the scope of the evaluated methods and datasets would improve the scientific rigor of the manuscript.
