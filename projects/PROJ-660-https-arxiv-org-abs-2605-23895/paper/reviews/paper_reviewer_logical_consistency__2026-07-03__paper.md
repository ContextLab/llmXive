---
action_items:
- id: c42ad78ce4a3
  severity: science
  text: The voxel selection rule (S_causal > 0) in Sec 3.2 does not logically enforce
    high activation. A silent voxel with low response to both positives and negatives
    yields a positive causal score but is not a representation. The conclusion that
    selected voxels represent the concept is unsupported without an explicit activation
    threshold.
- id: 13f375d63521
  severity: science
  text: The claim that 70% of activation-based findings are false positives (Sec 4.1)
    assumes negative controls are perfect. Since Appendix A.6 admits semantic-negative
    generation fails for broad concepts, a low causal score may reflect failed controls
    rather than true false positives. The conclusion is not fully supported without
    validating control quality.
- id: d1b88624b65e
  severity: science
  text: The statistical test in Appendix A.7 compares target scores against baselines
    on the *same* region selected to maximize the target score. This circular logic
    inflates significance. The p-value does not prove causal specificity independent
    of selection bias, undermining the claim of rigorous validation.
artifact_hash: 3e7821bc4196322444417ea380054aced908f7d581b2fd2f7cbee1140a5fd1b0
artifact_path: projects/PROJ-660-https-arxiv-org-abs-2605-23895/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T16:18:11.772666Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a compelling argument for moving from activation-based to causal-based discovery of visual representations. However, there are logical gaps in the derivation of the selection criteria and the interpretation of the validation results.

First, the definition of the "causal score" in Section 3.2 (lines 235-238) creates a logical vulnerability. The authors define the causal score as the average of the semantic-negative and counterfactual scores and select voxels where this score is positive. Logically, a voxel that is unresponsive to *all* stimuli (low activation to positives and low activation to negatives) would yield a causal score near zero or positive (if noise favors negatives slightly less), yet it would not represent the concept. The text implies that high activation is a prerequisite, but the mathematical selection rule ($S_{causal} > 0$) does not strictly enforce a minimum activation threshold. Therefore, the conclusion that the selected voxels are "representations" does not necessarily follow from the stated selection mechanism.

Second, the claim in Section 4.1 that activation-based methods yield a ~70% false positive rate relies on the assumption that a negative causality score definitively proves a region is not a true representation. This logic holds only if the "semantic negatives" and "counterfactuals" are perfect controls. The paper admits in Appendix A.6 that semantic-negative generation fails for broad concepts (e.g., "sky" or "reflection"). If the negative generation fails (e.g., the "negative" image still contains the target concept), the causal score will be low, leading the method to classify a true positive as a false positive. The conclusion that these are "false positives" rather than "false negatives of the validation test" is not fully supported without a rigorous analysis of the failure modes of the negative generation pipeline.

Finally, the statistical testing in Appendix A.7 (lines 630-640) compares the target concept score against a baseline of other concepts on the *same* region. Since the region was selected specifically to maximize the target score, this comparison is logically circular. The p-value tests whether the target is the *most* activating concept for that specific region, which is a tautology of the selection process. It does not logically prove that the region is causally specific to the target in a general sense, only that it is the best match among the tested concepts for that specific voxel set. The claim of "significance" requires a correction for the selection bias or a hold-out set that was not used in the region definition.
