---
action_items:
- id: c44232b7c48b
  severity: writing
  text: "In Section 4.2 (DG-WGPO), the text states the WER-gated threshold is set\
    \ to \u03C4=0.3, but Table 3 (tab:dg_wgpo_reward_hparams) in the Appendix lists\
    \ \u03C4=0.5. This contradiction must be resolved to ensure the reported hyperparameters\
    \ match the experimental setup."
- id: 7acda04af61a
  severity: writing
  text: The abstract and Section 3 claim the dataset covers '7 classic acoustic phenomena,'
    yet Table 1 (tab:primitive_effects) in the Appendix lists '8 primitive effects'
    before aggregation. Clarify whether one effect was merged or excluded to ensure
    the count of 7 is accurate and consistent with the simulation pipeline.
- id: 16d0d80c7a30
  severity: writing
  text: "Section 4.2 claims that errors shift 'abruptly' at WER > 30%, justifying\
    \ the gated reward. However, the ablation study in Table 2 (tab:hp-tau) shows\
    \ only a marginal WER difference (7.68 vs 7.64) between \u03C4=0.2 and \u03C4\
    =0.3. The text should temper the claim of an 'abrupt' shift or provide stronger\
    \ evidence that the 30% threshold is the critical inflection point."
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:53:14.762212Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several specific factual claims regarding dataset composition, hyperparameter settings, and the justification for methodological choices that require verification against the provided text and tables.

First, there is a direct contradiction regarding the WER-gated threshold ($\tau$) used in the Dual-Granularity WER-Gated Policy Optimization (DG-WGPO). The main text in Section 4.2 explicitly states: "We set the three hyperparameters as $\tau = 0.3$..." However, Table 3 in the Appendix (labeled `tab:dg_wgpo_reward_hparams`) lists the "WER gate threshold $\tau$" as **0.5**. Since the ablation study in Table 2 (`tab:hp-tau`) shows that $\tau=0.3$ yields the best result (7.64 WER) compared to 0.2, 0.4, and 0.5, it is likely the text is correct and the table is a typo. However, this discrepancy must be resolved to ensure the reproducibility of the reported results.

Second, the count of acoustic phenomena is inconsistent. The Abstract and Section 3 state that the `Voices-in-the-wild-2M` dataset covers **7** classic acoustic phenomena. However, Table 1 in the Appendix (`tab:primitive_effects`) lists **8** primitive effects (Additive noise, Echo delay, Reverberation, Nonlinear distortion, Resampling, Spectral filtering, Loudness transformation, Frame-level stutter). While the text mentions these are mapped to 7 "atomic" effects, the transition from 8 primitives to 7 atoms is not explicitly detailed in the main text, creating ambiguity about which primitive was merged or excluded. The claim of "7 phenomena" should be clarified to align with the 8 primitives listed in the appendix.

Third, the justification for the 30% WER threshold relies on the claim that error modes shift "abruptly" beyond this point. While the authors propose a gated reward to handle this, the sensitivity analysis in Table 2 (`tab:hp-tau`) shows that varying $\tau$ between 0.2 and 0.4 results in very small WER differences (7.68 to 7.64). The term "abrupt" suggests a sharp discontinuity that the provided data does not strongly support. The claim should be moderated to reflect that the threshold was empirically optimized rather than being a distinct, sharp boundary in error behavior.

Finally, the claim in the Abstract that the dataset includes "54 physically plausible compound scenarios" is supported by the enumeration in the Appendix (`tab:compound_scenario_count`), which sums to 54. This claim is accurate. The citation of external datasets (e.g., MUSAN, DNS) and the specific WER numbers in the main tables appear consistent with the provided text, though the specific values in the "Case Study" (e.g., 100.0% WER for Qwen3-ASR) are presented as qualitative examples and are not contradicted by the tables.
