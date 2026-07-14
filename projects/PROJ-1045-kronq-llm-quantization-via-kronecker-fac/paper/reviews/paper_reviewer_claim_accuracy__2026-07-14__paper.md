---
action_items:
- id: d70354f96f92
  severity: writing
  text: Abstract claims GPTQ/GPTAQ produce '>2000 perplexity' on LLaMA-3-70B at 2-bit,
    but Table 1 shows GPTQ at 2560.14 and GPTAQ as 'NaN'. Clarify that GPTQ yields
    ~2560 PPL while GPTAQ diverges (NaN) to accurately reflect the distinct failure
    modes.
- id: eb530969ff69
  severity: writing
  text: Abstract and Section 5.1 cite 7.93 perplexity for LLaMA-3-70B at 2-bit, but
    the primary Table 1 reports 8.43. The 7.93 value appears only in the Appendix.
    Update the abstract and text to cite the primary table value (8.43) or explicitly
    distinguish the sources.
- id: 0ad2890746c9
  severity: writing
  text: Section 5.1 states KronQ 'nearly doubles' GPTAQ on LiveCodeBench, but Table
    4 shows >2x gains (37.3 vs 16.3 and 22.3 vs 9.6). Change 'nearly doubles' to 'more
    than doubles' to accurately reflect the magnitude of improvement shown in the
    data.
artifact_hash: 6bdf7827fba12b0d8bdf1afc2ca37e869d5688f3fbc4e54d47c586b30e10b890
artifact_path: projects/PROJ-1045-kronq-llm-quantization-via-kronecker-fac/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-14T03:57:49.190091Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a robust technical argument for incorporating gradient covariance into the quantization objective, with sound mathematical derivations and consistent internal logic. However, there are minor discrepancies between the summary claims in the abstract and main text versus the specific numerical results reported in the primary tables.

First, the abstract and Section 5.1 state that KronQ achieves a perplexity of 7.93 on LLaMA-3-70B at 2-bit quantization. This value is found in the Appendix (Table 1 in `weight_only_zs`), but the primary results table (Table 1 in the main text) reports 8.43 for the same configuration. Since the main table is the primary evidence, the abstract and text should align with it or explicitly clarify the source of the discrepancy.

Second, the abstract claims that GPTQ and GPTAQ produce "degenerate quantizations (>2000 perplexity)" on LLaMA-3-70B. The data shows GPTQ at 2560.14 (consistent with the claim) but GPTAQ as "NaN" (indicating divergence). Conflating a specific high perplexity value with a complete divergence in the abstract slightly misrepresents the distinct failure modes observed.

Finally, the claim that KronQ "nearly doubles" the GPTAQ score on LiveCodeBench is an understatement; the data shows improvements of over 2x for both models tested. Using "more than doubles" would be a more precise description of the results.

These issues are minor and fixable through text edits, but they affect the precision of the paper's claims relative to its evidence.
