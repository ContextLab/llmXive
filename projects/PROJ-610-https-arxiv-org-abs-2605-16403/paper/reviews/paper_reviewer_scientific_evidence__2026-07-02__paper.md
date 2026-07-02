---
action_items:
- id: d15c1cea0d7c
  severity: science
  text: The paper claims a 28 percentage point average gain across Shift, Mute, and
    Swap interventions (Abstract, Sec 3.4), but Table 1 only reports baseline 'Avg
    Gap' values. The post-training accuracy for Mute and Swap is missing from the
    main results table, making the 28% aggregate claim unverifiable from the provided
    text.
- id: 42b6e81d7399
  severity: science
  text: The annotation protocol relies on 'human inspection' for audio timestamps
    (Sec 3.2, App B) but does not report inter-annotator agreement (IAA) statistics.
    Without IAA scores (e.g., Cohen's Kappa) or a description of the human verification
    process, the ground truth reliability for the preference pairs is unquantified.
- id: 1944d2e06459
  severity: science
  text: The study evaluates 6 models but provides no statistical significance testing
    (e.g., paired t-tests or bootstrap confidence intervals) for the reported accuracy
    differences. Given the large variance in model sizes (9B to 311B) and the binary
    nature of some metrics, point estimates alone are insufficient to claim robust
    superiority.
- id: cc2340c56e23
  severity: science
  text: The 'Limitations' section (App E) admits the Mute/Swap training study is incomplete,
    yet the Abstract and Conclusion present the 28% gain as a definitive result. The
    evidence presented in the tables does not support the magnitude of the claim for
    all three intervention types equally.
artifact_hash: e83058c54d1a49095166f0ef2ff7177a4db8d52f3626563ad7ae59fa949315e9
artifact_path: projects/PROJ-610-https-arxiv-org-abs-2605-16403/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:16:40.184212Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling diagnostic framework (\Thud) for identifying the "Clever Hans" effect in audio-visual MLLMs. The intervention design (Shift, Mute, Swap) is logically sound and effectively isolates visual priors from audio grounding. However, the scientific evidence supporting the central claim of a "28 percentage point" improvement across all three dimensions is currently incomplete and lacks necessary statistical rigor.

First, the quantitative evidence for the claimed 28% average gain is not fully presented. While Table 1 (Sec 4.1) provides detailed baseline performance and the "Avg Gap" for all models, it does not report the post-training accuracy for the Mute and Swap conditions. The text in Section 4.3 states that adding Mute/Swap SFT yields this gain, but without the corresponding numbers in a results table, the magnitude of the improvement for these specific interventions cannot be independently verified. The current data only robustly supports the improvement in the "Sync" (Shift) dimension.

Second, the ground truth construction relies on "human inspection" for audio event timestamps (Section 3.2, Appendix B) but fails to report inter-annotator agreement (IAA) metrics. In a study focused on temporal precision (e.g., $\epsilon_a = 0.5$s), the reliability of the human labels is critical. The absence of Kappa scores or a description of the adjudication process leaves the quality of the preference pairs ($y^+$ vs $y^-$) unquantified.

Third, the results are presented as point estimates without measures of variance or statistical significance. Given the binary nature of the diagnostic tasks (synced vs. desynced) and the potential for variance across different video samples, the lack of confidence intervals or significance testing (e.g., paired t-tests) makes it difficult to assess the robustness of the reported gains, particularly for the smaller models where sample sizes might be limiting.

Finally, there is a tension between the definitive claims in the Abstract/Conclusion and the admission in the Limitations (Appendix E) that the Mute/Swap training study is "incomplete." The evidence provided does not yet fully support the broad claim that the recipe successfully cures all three types of shortcuts to the same degree.
