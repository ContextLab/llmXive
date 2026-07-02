---
action_items:
- id: 098cdaab2d9f
  severity: writing
  text: Abstract claims +10.2% WebShop-Acc gain for 7B. Table 1 confirms Qwen2.5-7B
    gain is +10.2 (82.8 vs 72.6). However, Qwen3-1.7B gain is +20.3. Clarify if +10.2%
    applies only to 7B or if the text implies uniform gains.
- id: 5ed511dc5372
  severity: science
  text: Section 3.1 attributes GRPO+OPSD degradation on Qwen3-1.7B to 'unbounded distillation
    gradients'. While the performance drop (32.0 vs 46.1) is correct, no gradient
    norm evidence is provided. Soften to 'likely due to' or add gradient analysis.
- id: 452424c81ff8
  severity: fatal
  text: Section 3.1 claims Skill-GRPO shows a 'massive performance drop when tested
    without skills (60.2 vs 80.5)'. Table 1 shows Skill-GRPO (with skills) is 60.2
    and Skill-GRPO* (without) is 80.5. The text implies 60.2 is the 'without' score,
    which is false. Performance actually improves without skills. This contradicts
    the 'internalization' argument and misrepresents the data.
- id: 3f85c4eb4590
  severity: writing
  text: Section 3.3 claims Random Retrieval yields 'notable gains' of +1.0 on WebShop-Acc.
    Table 2 confirms +1.0 (73.6 vs 72.6). While numerically correct, 'notable' is
    subjective for such a small margin. Ensure consistency in describing small gains.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:57:18.827407Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with the provided evidence (tables, figures, and text).

**Critical Factual Error in Claim Interpretation (Fatal):**
In Section 3.1 ("Skills Internalization"), the paper claims: "While Skill-GRPO shows a massive performance drop when tested without skills (e.g., 60.2 vs. 80.5 on ALFWorld-3B)..."
- **Evidence:** Table 1 (Qwen2.5-3B, ALFWorld) lists `Skill-GRPO` (with skills) as **60.2** and `Skill-GRPO*` (without skills) as **80.5**.
- **Analysis:** The data shows that the model performs *better* (80.5) when skills are *removed* at inference compared to when they are present (60.2). The text claims there is a "performance drop when tested without skills," which implies the score should be lower without skills. The text has either swapped the numbers or misinterpreted the direction of the change. If the claim is that the model *relies* on skills, the data contradicts this (since performance drops *with* skills). If the claim is that the model *internalizes* skills (as the section title suggests), the data for Skill-GRPO (the baseline) actually shows it *fails* to internalize and is harmed by the skills at inference. The text's description of the baseline's behavior is factually inverted relative to the table. This undermines the comparison made to SDAR, which is claimed to "internalize" knowledge.

**Ambiguity in Performance Gains (Writing):**
The Abstract and Section 3.1 state SDAR achieves "+10.2% on WebShop-Acc" for 7B models.
- **Evidence:** Table 1 shows Qwen2.5-7B: SDAR (82.8) vs GRPO (72.6) = +10.2. Qwen3-1.7B: SDAR (58.6) vs GRPO (38.3) = +20.3.
- **Analysis:** The number +10.2 is correct for the 7B model. However, the phrasing "for 7B" in the abstract is slightly ambiguous given the 1.7B model shows a much larger gain. While not strictly false, it could be clarified to avoid implying the gain is uniform or that the 1.7B gain is not significant.

**Causal Attribution (Science):**
Section 3.1 attributes the degradation of "naive GRPO+OPSD" on Qwen3-1.7B (32.0 vs 46.1) specifically to "unbounded distillation gradients."
- **Analysis:** While the performance drop is real (32.0 < 46.1), the paper does not present direct measurements of gradient norms for the GRPO+OPSD baseline to prove they were "unbounded." The claim is a plausible hypothesis based on the method's design (lack of gating), but stating it as a definitive cause without empirical gradient evidence is a slight overreach. It should be framed as a likely cause or supported by gradient analysis.

**Minor Numerical Verification:**
The claims regarding Random Retrieval gains (+1.9, +1.6, +1.0) in Section 3.3 align perfectly with Table 2. The descriptor "notable" for a +1.0 gain is subjective but acceptable in context.

**Conclusion:**
The fatal error in interpreting the Skill-GRPO vs. Skill-GRPO* results (claiming a drop when the data shows an increase, or misidentifying which condition corresponds to which score) invalidates the specific argument about "internalization" in the baseline comparison. This requires a correction of the text to accurately reflect the table data.
