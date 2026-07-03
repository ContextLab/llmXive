---
action_items:
- id: 5f17de0fb910
  severity: science
  text: Clarify that the '70% false positive' claim (Sec 1) reflects failure against
    *generated* alternatives, not ground-truth biological false positives, to avoid
    overclaiming about prior literature validity.
- id: c958c498e523
  severity: science
  text: The statistical test in Appx S.5.5 compares target vs. other concepts on the
    same region. Add a null distribution test (e.g., shuffled labels) to rigorously
    rule out noise or random concept responses as the driver of specificity.
- id: 4141aad2bc26
  severity: science
  text: Quantify how semantic-negative generation failures (Appx S.5.4) impact the
    reported false positive rate. If 'hardest negatives' are actually positives due
    to generation errors, causal scores are biased; a sensitivity analysis is required.
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T16:20:47.285666Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling methodological shift from activation maximization to causal testing for visual concept discovery in fMRI. The sample size (4 subjects from NSD, ~10k images each) is robust, and the use of held-out generated data for validation is a strong design choice. However, the strength of the scientific evidence is currently limited by the reliance on generative models to define the "ground truth" of the counterfactuals.

The central claim—that 70% of activation-based discoveries are false positives (Section 1, line 45)—is derived from the observation that these regions fail to show a positive causal score on generated semantic negatives. While the logic is sound, the evidence is only as strong as the generated negatives. The authors acknowledge in Appendix S.5.4 that semantic-negative generation fails for broad concepts (e.g., "sky", "reflection"), where the generated "negative" still contains the target. If the "hardest negative" used to calculate the causal score (Section 3.2) is actually a positive image due to generation failure, the causal score will be artificially low, potentially misclassifying a true positive as a false positive. The manuscript needs a quantitative analysis of how generation failure rates correlate with the reported false positive rates to ensure the 70% figure is not an artifact of the generative model's limitations.

Furthermore, the statistical testing in Appendix S.5.5 compares the target concept score against a baseline of "other concepts" on the same region. This demonstrates selectivity relative to the tested set but does not fully rule out that the region is responding to a confounding low-level feature shared by the target and the baseline. A more rigorous null model, such as comparing against shuffled concept labels or a set of random noise concepts, would strengthen the claim that the discovered regions are truly concept-specific rather than just "different from the other 259 concepts."

Finally, the effect sizes reported in Table 1 are substantial, but the variance across subjects (Table S.4) shows some inconsistency. While the trend is consistent, a formal interaction test or confidence intervals on the mean differences would provide stronger evidence for the robustness of the causal advantage across the population.
