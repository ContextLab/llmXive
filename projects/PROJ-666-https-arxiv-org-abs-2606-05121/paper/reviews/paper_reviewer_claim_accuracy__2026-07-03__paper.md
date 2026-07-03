---
action_items:
- id: cbed0d3a8bb8
  severity: writing
  text: "In Section 3.2 (Streaming Data Construction), the text claims the TFJP module\
    \ uses 'half-chunk alignment \u03B4=1/2 of Audio-Interaction'. This is semantically\
    \ incorrect; \u03B4 is a time duration (200ms), not a fraction of the model. The\
    \ text should read '\u03B4=1/2 of the chunk size' or '\u03B4=200ms' to match the\
    \ Appendix and Algorithm 1."
- id: 506ab213b4d9
  severity: writing
  text: Table 1 (MMAU) and the Abstract claim Audio-Interaction achieves 58.15 on
    MMAU, surpassing Qwen2.5-Omni-3B (57.81). However, the table shows Qwen2.5-Omni-7B
    achieving 65.60. The claim 'surpasses them' is ambiguous and potentially misleading
    if interpreted as surpassing all baselines. Clarify that it surpasses the 3B initialization
    and specific 7B models in audio-instruction settings, not all 7B models generally.
- id: 11440d760af3
  severity: writing
  text: Section 4.2 claims the model improves over initialization by '+15.72/+17.04
    BLEU' on CoVoST2. Table 2 shows Audio-Interaction (55.22/35.21) vs Qwen2.5-Omni-3B
    (39.50/18.17). The math holds (55.22-39.50=15.72), but the text implies this is
    a general improvement over 'its initialization' without explicitly stating the
    baseline is the 3B version, which could be confused with the 7B version (41.40/29.40)
    where the gain is smaller. Explicitly cite the 3B baseline in the text.
- id: 649d9613398e
  severity: writing
  text: The Abstract states StreamAudio-2M is a '2.6M-item' corpus, but Figure 3 caption
    and Table 3 in the Appendix list '2.34M items'. This numerical inconsistency between
    the abstract, main text, and appendix tables must be resolved.
artifact_hash: d722b827ffcc42ef33cad3308518a181a01c5d135cbbac51efaf0289e64033d0
artifact_path: projects/PROJ-666-https-arxiv-org-abs-2606-05121/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T00:09:40.380156Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with cited evidence and internal consistency.

**Internal Consistency of Numerical Claims:**
There is a significant discrepancy regarding the size of the `StreamAudio-2M` dataset. The Abstract and Section 3.1 explicitly state the corpus comprises **2.6M items**. However, the caption for Figure 3 (StreamAudio-2M statistics) and the summary row in the table within Section 3.1 (Figure 3) state **2.34M items**. The Appendix Table `tab:app:sources` lists specific item counts that sum to approximately 2.34M (e.g., 539k+487k+382k+357k+270k+171k+130k ≈ 2.336M). The claim of 2.6M in the abstract appears to be an overstatement or a rounding error that contradicts the detailed breakdown provided in the figures and tables. This needs correction to ensure the abstract accurately reflects the data presented in the body.

**Precision of Comparative Claims:**
In the Abstract and Section 4.2, the authors claim `Audio-Interaction` "surpasses" state-of-the-art models on MMAU, citing 58.15 vs 57.81. While 58.15 is indeed higher than the 3B initialization (Qwen2.5-Omni-3B at 57.81), Table 1 clearly shows that `Qwen2.5-Omni-7B` achieves **65.60** and `Audio-Reasoner` achieves **61.71**. The phrasing "surpasses them" (referring to "state-of-the-art models") is ambiguous and risks misleading the reader into thinking the proposed model outperforms all listed baselines, including the 7B variants. The claim should be qualified to specify that it surpasses the *3B initialization* and performs competitively against 7B models, rather than broadly "surpassing" SOTA.

**Semantic Accuracy of Technical Descriptions:**
In Section 3.2, the description of the Time-frequency joint preprocessing (TFJP) module states: "refining both boundaries with half-chunk alignment $\delta=\frac{1}{2}$ of \textsc{Audio-Interaction}". This is factually incorrect. $\delta$ is a time parameter (defined as 200ms in the Appendix and Algorithm 1), representing half the *chunk size* (400ms), not half of the *model* (`Audio-Interaction`). This is a semantic error in the prose that misrepresents the variable's definition. It should be corrected to "half-chunk alignment $\delta=200$ms" or "half the chunk size".

**Citation Support for Performance Gains:**
The claim in Section 4.2 regarding the BLEU score improvement on CoVoST2 ("+15.72/+17.04") is mathematically accurate when comparing `Audio-Interaction` to `Qwen2.5-Omni-3B` (the initialization). However, the text refers to "its initialization" without explicitly naming the 3B variant. Given that the paper also compares against 7B models, and the 7B initialization (`Qwen2.5-Omni-7B`) has significantly higher baseline scores (41.40/29.40), the claim could be misinterpreted. The text should explicitly state "improves over its 3B initialization" to prevent confusion with the 7B baseline performance.

Overall, the core scientific claims are supported by the provided tables, but the manuscript contains inconsistencies in dataset size reporting and ambiguous phrasing in comparative claims that require clarification to ensure factual accuracy.
