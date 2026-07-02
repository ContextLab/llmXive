---
action_items:
- id: 540aad46f167
  severity: writing
  text: The '18.7% improvement' claim (Sec 1, 4.2) lacks a clear baseline. Table 1
    shows a rise from 0.725 to 0.861 (18.8% relative to 0.725), but the text implies
    a comparison to 'SOTA' which is ambiguous. Explicitly state the baseline value
    used for this percentage to avoid over-claiming magnitude.
- id: 96f430f79dad
  severity: writing
  text: The claim of 'comprehensive outperformance' (Sec 1, 4.2) is contradicted by
    Table 1, where the method underperforms in In-Domain DINO-I (0.400 vs 0.407) and
    CLIP-I (0.690 vs 0.701). Qualify the text to reflect that improvements are specific
    to cross-domain scenarios, not universal.
- id: 9ff6e8e6a207
  severity: writing
  text: The ablation study (Sec 4.3) claims CCL 'significantly' improves fidelity
    by 0.3% and 1.5% while stating it mainly improves controllability. These negligible
    gains contradict the 'significant' framing. Temper the language regarding fidelity
    improvements attributed to CCL.
artifact_hash: 94f10ea6969d9a855608669bc738975c27d93327dc527ce8f35f4b9e47a4390d
artifact_path: projects/PROJ-791-https-arxiv-org-abs-2606-26058/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T13:44:42.713121Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

"The paper exhibits a tendency to over-claim the universality and magnitude of its results, particularly in the Introduction and Experimental sections.

First, the headline statistic of an \"18.7% improvement in Cross-Domain Score\" (Introduction, Section 4.2) is ambiguous. In Table 1, the CD-Score rises from 0.725 (Kling 1.6) to 0.861 (Ours). While this is an ~18.8% relative increase over Kling, the phrasing \"over SOTA\" is confusing without explicitly stating the baseline. If the authors intended to compare against the best open-source baseline (VACE-Wan2.2 at 0.546), the improvement is actually ~57%. This lack of precision risks overstating the specific gain relative to the most relevant competitor.

Second, the authors claim the method \"comprehensively outperforms existing methods\" (Introduction, Conclusion). However, Table 1 clearly shows that DomainShuttle does not outperform all baselines in every metric. Specifically, in In-Domain Subject Consistency, the method scores 0.400 on DINO-I (worse than SkyReels-V3's 0.407) and 0.690 on CLIP-I (worse than Phantom's 0.701). The use of \"comprehensively\" is an overreach given these specific deficits. The narrative should be adjusted to highlight that the method excels in *cross-domain* flexibility while maintaining *competitive* (not superior) in-domain fidelity.

Finally, the ablation study description for Cross-Pair Consistent Loss (CCL) contains contradictory framing. The text states CCL \"mainly improves controllability... rather than fidelity,\" yet immediately cites \"0.3% (CLIP) and 1.5% (DINO)\" improvements as evidence of its efficacy. Describing a 0.3% gain as a significant contribution to fidelity is an over-interpretation of the data. The authors should clarify that CCL's primary value is in cross-domain consistency, and the minor fidelity gains are incidental, rather than framing them as a dual optimization of both."
