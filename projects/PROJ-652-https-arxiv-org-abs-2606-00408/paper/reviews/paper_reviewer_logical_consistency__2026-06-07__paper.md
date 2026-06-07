---
action_items:
- id: 912f9fc471cd
  severity: writing
  text: Clarify the definition of 'middle observations' in the masking mechanism (Eq
    2 vs Section 6.1). The paper masks 'earlier' observations (turns 1 to t-K), which
    includes both 'first' and 'middle' trajectory pages. However, Section 6.1 claims
    masking targets 'neglected middle observations' while Fig 3 notes agents re-open
    'first pages'. This creates ambiguity about whether 'first' pages are also masked
    and how this relates to the 'Collapse' regime.
- id: 60db9f39f199
  severity: writing
  text: Align the qualitative description in Figure 1 caption ('CM adds little') with
    the quantitative data in Section 5 ('+6.2 to +6.6 pts'). A 6-point gain is substantial
    relative to the baseline, and 'little' may understate the 'plateau' regime's benefit
    compared to the 'Middle' regime (+11.7 pts).
- id: 9b31075ba683
  severity: science
  text: Ensure the 'Signal-to-Noise Ratio bottleneck' claim (Section 6.2) is clearly
    linked to the 'Regime Map' (Section 5). The text states SNR optimization is the
    bottleneck, yet masking (an SNR optimizer) fails in the Saturated regime. Clarify
    that SNR optimization is beneficial *only* when the model's filtering capacity
    is insufficient (Middle regime), rather than being a universal bottleneck.
artifact_hash: 0662f086c971957827b984215e812ef5eb19c982637f2c1511efa72d77075eda
artifact_path: projects/PROJ-652-https-arxiv-org-abs-2606-00408/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-07T21:39:49.147549Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

This review focuses strictly on the logical consistency of the paper's claims, evidence, and mechanisms.

**Logical Consistency Assessment**

The paper presents a coherent logical framework connecting the intervention (observation masking) to the observed outcomes (regime map) via a proposed mechanism (attention/token trade-off). The core argument—that masking helps only when the model cannot filter noise but harms when it needs to retrieve specific evidence—is well-supported by the case studies (Section 1) and the quantitative regime boundaries (Section 5). The attention analysis (Section 6.1) logically supports the safety of masking old tokens by showing lower attention weights on non-recent observations.

However, there are minor logical ambiguities in how the masking window interacts with specific trajectory positions ("first" vs. "middle" pages) and how the "SNR bottleneck" claim relates to the regime-dependent failure in saturated models.

**Specific Concerns**

1.  **Masking Target Definition (Section 6.1 vs Eq 2):** Equation 2 defines masking as replacing observations outside a retention window $K$ (i.e., turns $1$ to $t-K-1$). This includes both the "first" pages of the trajectory and the "middle" pages. However, Section 6.1 states "Masking targets neglected middle observations," and Figure 3 notes agents "re-open latest or first pages." If "first pages" are also masked (as they are outside $K$), the claim that masking targets "middle" observations is imprecise. The logic holds that *neglected* pages are masked, but the text should clarify that "first pages" are also masked and that the "Collapse" regime occurs specifically when these "first pages" contain crucial signals that the model *does* need to re-open, contradicting the general "neglected" trend.
2.  **Gain Magnitude Phrasing (Figure 1 vs Section 5):** The Figure 1 caption describes the "Retriever bottleneck plateau" as a regime where "CM adds little." However, Section 5 quantifies this gain as $+6.2$ to $+6.6$ points. Compared to the peak gain of $+11.7$ points, this is roughly 50%, but compared to a baseline of 0%, it is a significant improvement. Using "little" may logically understate the benefit in this regime, potentially confusing the reader about the magnitude of the "plateau."
3.  **SNR Bottleneck vs. Regime Collapse (Section 6.2 vs Section 5):** The paper claims "optimizing signal-to-noise ratio is the bottleneck for advanced agents" (Section 5). Yet, in the "Model-saturated" regime, masking (which optimizes SNR by removing noise) fails or harms performance (Section 5). The regression probe (Section 6.2) shows high AUC for these models, implying SNR *is* separable, but gain is low. The logic requires clarification: Is SNR the bottleneck only for *mid-capacity* models? If so, the claim should be refined to "SNR optimization is the bottleneck *conditional on model capacity*," to avoid implying masking should always help with SNR.

**Conclusion**

The logical structure is sound, but clarifying the interaction between the masking window and specific trajectory pages ("first" vs. "middle") and refining the "SNR bottleneck" claim to account for the saturated regime will strengthen the logical consistency.
