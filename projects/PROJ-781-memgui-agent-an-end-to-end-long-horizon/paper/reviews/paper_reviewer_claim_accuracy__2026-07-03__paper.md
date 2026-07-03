---
action_items:
- id: de52b5f44d3c
  severity: writing
  text: Clarify in Section 3.1 that the performance regression for smaller models
    (2B-8B) with CONACT is specific to the zero-shot setting, and that SFT (MemGUI-8B-SFT)
    reverses this trend, to avoid implying the architecture is inherently harmful.
- id: b9c20f417622
  severity: science
  text: In Section 4.1, verify that 'Qwen3-VL-8B-Instruct' is the only relevant open-data
    8B baseline omitted from Table 2. If other open-data 8B models exist (e.g., UI-Venus),
    either include them or qualify the 'best among open-data' claim to reflect the
    specific baselines compared.
- id: 2dcbb181bc8d
  severity: writing
  text: In Section 4.3, clarify that the reported gains for 'history folding' (+5.0%)
    and 'self-describing steps' (+7.5%) are marginal improvements in the sequential
    ablation, not independent additive contributions to the ReAct baseline.
- id: ba42cd33b8db
  severity: writing
  text: In Section 4.4, explicitly state that the -42% and -57% reductions for hallucination
    types refer to the decrease in the count of those specific errors, not their proportional
    contribution to the total 41% failure reduction, to prevent ambiguity.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:22:29.477441Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents several strong factual claims regarding performance gains and architectural impacts. Most claims are supported by the provided tables, but a few require clarification to ensure the evidence matches the strength of the assertions.

In Section 3.1, the claim that smaller models "regress" with CONACT is supported by Table 1, which shows a drop in Pass@1 for 2B, 4B, and 8B models. However, the text does not explicitly distinguish this as a zero-shot phenomenon, which is crucial because the subsequent section (3.2) introduces MemGUI-3K specifically to fix this. Without this distinction, a reader might incorrectly infer that the CONACT architecture is detrimental to smaller models in general, rather than just ineffective without the specific SFT data. The text should clarify that the regression is observed in the zero-shot setting and is reversed by the proposed SFT.

In Section 4.1, the claim that MemGUI-8B-SFT achieves the "best open-data 8B performance" is supported by Table 2, which compares it against Qwen3-VL-8B-Instruct. However, the Related Work section and the bibliography list other potential open-data 8B models (e.g., UI-Venus, Mobile-Agent-V3). The review cannot verify if these models were excluded from the comparison or if they simply performed worse. To support the "best among open-data" claim robustly, the authors should either include these models in the comparison table or explicitly state in the text that the comparison is limited to the specific baselines chosen and that other open-data models were considered but not included for specific reasons (e.g., lack of public weights, different benchmark settings).

In Section 4.3, the ablation study text states that "history folding adds 5.0%, and self-describing steps add 7.5%". The table shows these as cumulative improvements in a sequential ablation (Baseline -> +UI -> +History -> +Self). The phrasing "adds X%" could be interpreted as an independent contribution to the baseline, which is not what the table shows. The text should be refined to clarify that these are the marginal gains observed when adding each component to the *previous* configuration in the ablation sequence.

Finally, in Section 4.4, the claim about reducing failures by 41% is mathematically sound based on the numbers provided (99 to 58). The breakdown of reductions in process and output hallucination (-42% and -57%) is likely correct based on the figure, but the text should ensure it is clear that these percentages refer to the reduction in the *count* of those specific error types, not their contribution to the total reduction, to avoid any ambiguity in how the total 41% reduction is composed.

Overall, the claims are largely accurate, but minor clarifications in the text are needed to prevent misinterpretation of the data, particularly regarding the zero-shot vs. SFT performance of smaller models and the specific nature of the ablation gains.
