---
action_items:
- id: 817efc03c32f
  severity: science
  text: The empirical p-value method in Appendix A uses LLM-selected baselines rather
    than a null distribution. Clarify if this controls for confounds. Crucially, no
    multiple-comparison correction (e.g., FDR) is reported for the 260 concepts tested,
    which is vital given the claimed 70% false positive rate in baselines.
- id: be82bfb4f491
  severity: science
  text: Table 1 and ablation tables report mean scores without variance (SD/SE) or
    confidence intervals. Without error bars or statistical tests (e.g., paired t-tests)
    comparing methods across the 50 concepts, the significance of reported improvements
    (e.g., 0.62 vs -0.44) cannot be rigorously assessed.
- id: fce8f620df80
  severity: science
  text: The voxel selection threshold (S_causal > 0) in Sec 3.2 ignores the multiple
    testing problem across ~40k voxels. A permutation test or FDR control for voxel-wise
    selection is required to validate the reported false positive reduction and ensure
    the threshold is not arbitrary.
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T16:21:27.225403Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis framework in BrainCause introduces a novel causal scoring mechanism, but the manuscript lacks rigorous validation of significance and false discovery rate control.

First, the empirical p-value calculation in Appendix A (Section `sec_sup:statistical_test`) compares target scores against an LLM-defined baseline of "distinct concepts" rather than a null distribution (e.g., shuffled labels). This introduces dependency on the semantic similarity of the baseline set, which is unquantified. More critically, the authors test 260 concepts across 4 subjects (1,040 tests) but report no correction for multiple comparisons (e.g., Benjamini-Hochberg FDR). Given the central claim that activation-based methods have a ~70% false positive rate, the absence of FDR control on the proposed method's discoveries is a significant omission.

Second, quantitative results in Table 1 (`tab:quant_main`) and ablation tables (e.g., `tab_sup:Abaltion_scores`) report mean scores across concepts and subjects but omit measures of variability (standard deviation, standard error, or confidence intervals). The reported improvements (e.g., BrainCause causal score of 0.62 vs. MindSimulator's -0.44) appear substantial, but without error bars or reported statistical tests (e.g., paired t-test) comparing methods across the 50 concepts, the statistical significance of these differences remains unverified. The text mentions "statistical tests" in Section 3.3 but does not detail test statistics or p-values for the method comparisons.

Finally, the voxel selection criterion in Section 3.2 and Appendix A.4 relies on a deterministic threshold ($S_{causal}(v) > 0$) on a difference score derived from noisy fMRI predictions. The authors do not address the multiple testing problem inherent in selecting from ~40,000 voxels per subject. Without a permutation-based null distribution for voxel-wise scores or an FDR correction applied to the selection process, the reported "false positive" reduction may be an artifact of the thresholding method rather than a true causal effect. The authors should provide a permutation analysis to establish the null distribution of the causal score and apply appropriate multiple-comparison corrections.
