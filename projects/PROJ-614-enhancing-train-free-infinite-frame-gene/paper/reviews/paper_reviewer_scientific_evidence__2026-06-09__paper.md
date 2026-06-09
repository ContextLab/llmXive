---
action_items:
- id: daec83d23c43
  severity: science
  text: Add statistical significance testing (e.g., t-tests, confidence intervals)
    to all quantitative comparisons in Tables 1-3. Currently no p-values or error
    bars are reported for the claimed 4.7% S.C. improvement over FIFO-Diffusion.
- id: 91c5627b535d
  severity: science
  text: Report the exact number of evaluation prompts used for main VBench/NarrLV
    experiments (only 50% subset mentioned for ablations in App.~\ref{app:ab_exp_imp}).
    This affects reproducibility and claim robustness.
- id: bb45b0ed7176
  severity: science
  text: Address multiple comparison concerns in ablation studies. Tab.~\ref{tab:ab_zig_length}
    tests 6 $L_{\mathrm{zig}}$ values and Tab.~\ref{app:tab_2} tests 8 $\delta_{\mathrm{adju}}$
    values without correction for multiple testing.
- id: 6e1332814088
  severity: science
  text: Provide power analysis or sample size justification for the user study (48
    prompts, 8 annotators). Report confidence intervals for the percentage differences
    in Table~\ref{tab:user_study}.
artifact_hash: 2fc45fd89cfd8c3cc27102ad20713af6a66d4f721af1c258a0cd318f7ea682b3
artifact_path: projects/PROJ-614-enhancing-train-free-infinite-frame-gene/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T21:43:55.288228Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This re-review confirms that **none of the four prior action items** regarding scientific evidence have been adequately addressed in the current revision. The manuscript continues to present quantitative claims without the necessary statistical rigor to support them.

First, **statistical significance testing is still missing** from Tables 1-3 (`tab:vbench-results`, `tab:narrlv-results`, `tab:ab_1`). The claim of a "4.7% S.C. improvement over FIFO-Diffusion" (Introduction, Line 135) is presented as a deterministic fact, yet no p-values or error bars are provided to indicate whether this difference is statistically significant or potentially due to random variation across evaluation seeds. Without this, the SOTA claim is scientifically unsubstantiated.

Second, **reproducibility of the main experiments remains unclear**. While the appendix mentions a 50% subset for ablation studies (App. `app:ab_exp_imp`), the main VBench and NarrLV evaluations (Section 4.1) do not specify the exact number of prompts used. This ambiguity prevents independent verification of the reported scores.

Third, **multiple comparison issues persist** in the ablation studies. Table `tab:ab_zig_length` tests 6 values for $L_{\mathrm{zig}}$, and Table `app:tab_2` tests 8 values for $\delta_{\mathrm{adju}}$. The authors select optimal values based on peak performance without correcting for the increased Type I error risk inherent in testing multiple hyperparameters. This inflates the likelihood of finding spurious improvements.

Finally, the **user study lacks statistical validation**. Table `tab:user_study` reports percentages (e.g., 62.23% preference) from 48 prompts and 8 annotators but provides no confidence intervals or power analysis. With this sample size, the margin of error is substantial, and the text does not justify whether the study was powered to detect the reported differences.

Until these statistical gaps are resolved, the evidence for MIGA's superiority is insufficient. The central claims rely on point estimates without measures of uncertainty, making the results fragile to alternative explanations. Please address all four items in the next revision.
