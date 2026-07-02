---
action_items:
- id: 1ce90db82dc1
  severity: science
  text: "Inconsistent WER gate threshold: Section 4.2.2 defines the WER-gated fusion\
    \ threshold as \u03C4=0.3, but Appendix Table 4 (Reward hyperparameters) and the\
    \ text in Appendix Section 'Reward tuning and diagnostics' state \u03C4=0.5. This\
    \ contradiction undermines the reproducibility of the DG-WGPO mechanism."
- id: 8f33b9860a23
  severity: science
  text: 'Contradictory generation counts: Section 5.1 ''Implementation Details'' states
    K=16 rollouts per input, while Appendix Table 3 (DG-WGPO generation hyperparameters)
    lists ''Number of generations'' as 12. The effective batch size calculation in
    the same table (4x3x16=192) also conflicts with the stated 12 generations.'
- id: 7f540d1d4fb3
  severity: writing
  text: "Inconsistent hyperparameter reporting: Section 4.2.2 sets \u03B1_dyn=0.6\
    \ and \u03B1_s=0.4, which matches Table 4, but the text in Appendix 'Reward tuning\
    \ and diagnostics' repeats these values while the table caption for Table 4 lists\
    \ 'Low-WER fusion' as 0.75/0.25 and 'High-WER fusion' as 0.25/0.75, which is consistent,\
    \ but the text in Section 4.2.2 does not explicitly define the fusion weights,\
    \ only the threshold logic, creating ambiguity in the exact formula application."
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:52:49.034967Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent logical framework for addressing the "acoustic robustness bottleneck" by linking the failure modes of existing models (semantic collapse at high WER) to a specific architectural solution (Dual-Granularity WER-Gated Policy Optimization). The premise that standard WER rewards fail to provide gradients when WER > 30% is well-motivated by the observed shift from word-level errors to hallucinations. The proposed mechanism of switching reward granularity based on a WER threshold logically follows from this premise.

However, the internal consistency of the experimental reporting is compromised by significant contradictions in key hyperparameters, which prevents the verification of the causal claims made in the ablation studies.

First, there is a direct contradiction regarding the WER-gated threshold ($\tau$) used in the DG-WGPO reward function. In Section 4.2.2 ("WER-gated dynamic fusion"), the text explicitly states: "We set the three hyperparameters as $\tau = 0.3$..." and the fusion logic is defined around this value. However, in the Appendix, under the table "Reward hyperparameters used in DG-WGPO" (Table 4) and the accompanying text in "Reward tuning and diagnostics," the value is listed as $\tau = 0.5$. Since the ablation study in Table 2 (Sensitivity to gating threshold $\tau$) shows that $\tau=0.3$ yields the best result (7.64 WER) compared to $\tau=0.5$ (7.70 WER), the discrepancy between the main text's claim of using the optimal value and the appendix's reporting of a sub-optimal value (or vice versa) creates a logical gap. It is unclear which threshold was actually used to generate the "Mega-ASR (full)" results in Table 1.

Second, the number of rollouts ($K$) used during the RL training phase is inconsistent. Section 5.1 ("Implementation Details") states: "RL runs for 6,000 steps with... $K=16$ rollouts per input." Conversely, Appendix Table 3 ("Generation settings used in the main DG-WGPO run") lists "Number of generations" as 12. Furthermore, the "Effective prompt batch size" calculation in that same table is shown as $4 \times 3 \times 16 = 192$, which mathematically relies on $K=16$, yet the table explicitly lists 12 generations. This inconsistency casts doubt on the reproducibility of the training dynamics and the validity of the advantage estimation described in the methodology.

Finally, while the logic of the "Environment-Aware Routing" is sound (preserving clean-speech performance), the specific claim in Section 5.1 that routing "improves LibriSpeech WER from 1.78/3.57 to 1.63/3.37" requires scrutiny. The baseline Qwen3-ASR (Table 2) is listed as 1.62/3.07 (Dev) and 1.62/3.40 (Test). The "Ours w/ router" row shows 1.64/3.07 (Dev) and 1.63/3.37 (Test). The text claims an improvement from 1.78 (which matches the "Ours" without router Dev set), but the comparison baseline in the text (1.78) does not match the baseline model's reported score in the table (1.62). This suggests a potential confusion between the base model's performance and the non-routed model's performance in the narrative, weakening the logical support for the routing claim.

These inconsistencies do not necessarily invalidate the core scientific contribution but require clarification to ensure the reported results logically follow from the described experimental setup.
