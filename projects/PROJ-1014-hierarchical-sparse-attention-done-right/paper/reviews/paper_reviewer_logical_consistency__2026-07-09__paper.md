---
action_items:
- id: 9e4dfef66786
  severity: writing
  text: Section 4.1 claims HiLS-Attn 'sustains performance comparable to full attention'
    on MK-MQ, but Table 345M_main_ruler shows HiLS (95) vs Full-Attn (97). The text
    implies parity where the table shows a 2-point gap. Clarify if 'comparable' allows
    this margin or correct the claim.
- id: 65e61fdd81ab
  severity: writing
  text: Section 4.2 states HiLS 'consistently outperforms' Full-Attn HoPE, but Table
    345M_256K_ppl shows HiLS (7.51) vs Full-Attn HoPE (7.53) at 256K, a negligible
    0.02 difference. The 'consistent' claim is too strong given the mixed data. Qualify
    the claim to reflect the specific metrics where outperformance is significant.
- id: 2968f4c21449
  severity: writing
  text: Section 4.3 claims removing Q-Cal 'severely degrades performance' citing PPL,
    but Table 345M_ablation_ppl shows only a 0.03 PPL increase (4.94 to 4.97). The
    degradation is severe only in RULER scores (VT drops 72 to 49). Correct the text
    to specify the metric or downgrade the severity adjective for PPL.
artifact_hash: c95e527feac1da55ce3c1a4f78a6e7762db38d741afaaaef5a9558e2491c1f16
artifact_path: projects/PROJ-1014-hierarchical-sparse-attention-done-right/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-09T02:53:17.650262Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper's logical structure is generally sound, with the proposed method (HiLS-Attention) following logically from the identified limitations of existing sparse attention methods. The derivation of the LogSumExp surrogate provides a clear mathematical bridge between the problem and the solution.

However, there are minor inconsistencies between the textual claims and the reported numerical results in the experiments section, which constitute logical gaps in the argumentation:

1.  **Overstated Performance Parity:** In Section 4.1, the text claims HiLS-Attn "sustains performance comparable to full attention" on MK-MQ. While Table `345M_main_ruler` shows HiLS-Attn-HoPE achieving 100 on Single-Needle, it scores 95 on MK-MQ at 8K, whereas Full-Attn RoPE scores 97. The text implies a stronger parity than the data supports for the MK-MQ task.

2.  **Inconsistent "Consistent Outperformance" Claim:** Section 4.2 asserts that HiLS-Attn-HoPE "consistently outperforms" Full-Attn baselines. Table `345M_256K_ppl` shows that at 256K context, HiLS-Attn-HoPE has a PPL of 7.51, while Full-Attn HoPE has 7.53. This is a negligible difference, making the "consistent" claim ambiguous. The text should be more precise about which baselines are outperformed and by what margin.

3.  **Exaggerated Ablation Impact:** In Section 4.3, the text states that removing the low-rank query calibration (Q-Cal) "severely degrades performance." The ablation table (`345M_ablation_ppl`) shows the PPL at 8K increases from 4.94 to 4.97. This is a very small increase. While the RULER scores (specifically Variable Tracking) do drop significantly (from 72 to 49), the text cites the PPL table as the primary evidence for "severe" degradation. The logical link between the specific PPL numbers and the qualitative adjective "severe" is broken.

These issues do not invalidate the core thesis but represent minor logical overreaches in the interpretation of the results. Correcting the text to align precisely with the data tables will strengthen the paper's internal consistency.
