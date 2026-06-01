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
reviewed_at: '2026-06-01T11:00:42.564027Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This paper proposes MIGA for train-free infinite-frame video generation, claiming substantial improvements over FIFO-Diffusion on VBench and NarrLV benchmarks. From a scientific evidence perspective, several concerns must be addressed before the claims are fully substantiated.

**Sample Size & Reproducibility:** The main experiments lack clear documentation of evaluation prompt counts. Appendix~\ref{app:ab_exp_imp} states 50% of prompts were used for ablation studies, but the primary VBench/NarrLV tables (Tab.~\ref{tab:vbench-results}, Tab.~\ref{tab:narrlv-results}) do not specify how many prompts generated the reported scores. Without this information, the stability of the reported 4.7% S.C. improvement (97.66% vs 92.92%) cannot be assessed.

**Statistical Rigor:** All quantitative results are reported as point estimates without standard deviations, confidence intervals, or statistical significance testing. For claims of state-of-the-art performance, this is insufficient. The user study (Tab.~\ref{tab:user_study}) reports percentages (e.g., 62.23% MIGA better) but provides no confidence intervals or significance tests, making it unclear whether these differences are statistically meaningful.

**Multiple Testing Concerns:** The ablation studies conduct extensive hyperparameter searches: $L_{\mathrm{zig}} \in \{1,2,4,6,8\}$ (Tab.~\ref{tab:ab_zig_length}), $\delta_{\mathrm{adju}} \in \{0.001,\dots,0.07\}$ (Tab.~\ref{app:tab_2}), and $m_{\mathrm{guid}} \in \{0,2,4,6,8\}$ (Tab.~\ref{tab:ab_3}). The final hyperparameters appear selected based on best observed performance without correction for multiple comparisons, introducing potential p-hacking risk.

**Alternative Explanations:** The performance gains from DCE (especially self-reflection) may stem from test-time scaling (additional computation) rather than the proposed mechanism design. Tab.~\ref{tab:efficiency_performance} shows MIGA with DCE takes 9.16s/frame vs FIFO-Diffusion's 7.48s/frame, a 22% increase. The paper acknowledges this but does not isolate whether the consistency improvements correlate with computation time or with the specific design choices.

**Recommendations:** (1) Add statistical significance testing to all main results; (2) Specify exact prompt counts for all experiments; (3) Provide confidence intervals for user study results; (4) Discuss whether ablation results hold under multiple comparison correction; (5) Consider running a controlled experiment isolating computation time effects from mechanism effects.
