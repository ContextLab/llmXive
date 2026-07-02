---
action_items:
- id: bc6a6177623a
  severity: science
  text: The Cross-Domain (CD) Score relies on GPT-5.2, a model not publicly available
    or verifiable. To ensure scientific reproducibility, replace this with a fully
    open-source MLLM (e.g., Qwen-VL) for the primary metric or provide the exact model
    weights and inference code.
- id: 95a5e4575554
  severity: science
  text: The ablation study (Tab. 2) shows CCL improves CD-Score by 5.9% but only marginally
    affects in-domain fidelity. The paper claims CCL 'precisely extracts intrinsic
    features,' but the data suggests it primarily prevents overfitting to style. Clarify
    this distinction to avoid over-interpreting the loss function's mechanism.
- id: 761d6b0887cf
  severity: science
  text: The human preference study (Sec 4.3) uses 40 volunteers ranking 20 videos
    each without reporting inter-rater reliability (e.g., Krippendorff's alpha) or
    statistical significance tests (e.g., t-tests) between methods. Add these statistical
    validations to support the claim of 'significant advantages'.
artifact_hash: 94f10ea6969d9a855608669bc738975c27d93327dc527ce8f35f4b9e47a4390d
artifact_path: projects/PROJ-791-https-arxiv-org-abs-2606-26058/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T13:45:17.883233Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel architecture for open-domain subject-driven video generation, but the scientific evidence supporting the central claims requires strengthening in three key areas: metric reproducibility, statistical rigor in human evaluation, and precise interpretation of ablation results.

First, the primary metric for the paper's main contribution—the "Cross-Domain Score" (CD-Score)—relies on **GPT-5.2** (Section 4, "Evaluation Metrics"). As of the current scientific landscape, GPT-5.2 is not a publicly available or verifiable model. Relying on a closed, non-reproducible model for the primary quantitative claim (an 18.7% improvement) undermines the scientific validity of the result. The authors must either switch to a fully open-source, reproducible MLLM (such as Qwen-VL, which they mention as an alternative) for the primary metric or provide the exact model weights and inference scripts to allow independent verification.

Second, the **Human Preference Evaluation** (Section 4.3) lacks necessary statistical rigor. The study involves 40 volunteers ranking 20 videos each. While the results are presented as a bar chart (Fig. 5), the text claims "significant advantages" without reporting inter-rater reliability (e.g., Krippendorff's alpha) or statistical significance tests (e.g., paired t-tests or Wilcoxon signed-rank tests) between the proposed method and baselines. Without these metrics, the claim of statistical significance is unsupported.

Third, the interpretation of the **Cross-Pair Consistent Loss (CCL)** in the ablation study (Table 2) appears slightly overstated. The data shows CCL improves the CD-Score by 5.9% (from 0.813 to 0.861) but has a negligible effect on in-domain fidelity (DINO-I: 0.394 vs 0.400; CLIP-I: 0.688 vs 0.690). The text states CCL "precisely extracts intrinsic subject features," but the evidence suggests its primary function is preventing the model from copying style/irrelevant features (improving flexibility) rather than enhancing the core identity representation itself. The discussion should be refined to accurately reflect that CCL primarily drives *cross-domain flexibility* rather than general subject fidelity.

Finally, the sample size for the test set (110 in-domain, 110 cross-domain) is reasonable, but the authors should explicitly state the confidence intervals for the reported metric improvements in Table 1 to better contextualize the "significant" improvements claimed.
