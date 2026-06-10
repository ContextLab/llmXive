---
action_items:
- id: 97adae803bd1
  severity: science
  text: Add statistical significance testing (e.g., paired t-tests) for the main quantitative
    results in Tables 1 and 2 to confirm improvements are not due to variance.
- id: b7988d97a9c2
  severity: science
  text: Clarify whether single-view baseline restoration models (Restormer, HI-Diff,
    etc.) were fine-tuned on the specific motion blur distribution used in training
    to ensure a fair comparison.
- id: f209cf4cbe10
  severity: science
  text: Discuss the dependency of the Attention Alignment Loss on ground-truth geometry
    during training and how this impacts real-world deployment where GT is unavailable.
artifact_hash: 1b009a000ce5ea80de9107001816db5f680b271a1e700e1b78677c55727d55dc
artifact_path: projects/PROJ-632-https-arxiv-org-abs-2605-26230/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T11:58:15.898938Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: major_revision_science
---

The revision fails to address any of the three prior action items concerning scientific evidence, leaving the robustness of the central claims unsupported. First, quantitative results in Tables 1 and 2 (`tab/pose.tex`, `tab/recon.tex`) report point estimates (AUC, F-score) without statistical significance testing. Section 5.1 does not mention paired t-tests, bootstrapping, or confidence intervals. Without these metrics, it is impossible to determine if the observed improvements over baselines (e.g., GARD vs. VAE_MVD) are statistically significant or due to random variance, particularly given the variance inherent in diffusion-based generation. 

Second, Section 5.1 (`sec/5_exp.tex`) remains insufficient regarding baseline training protocols. It states that single-view models (Restormer, HI-Diff) are "instantiated," but does not clarify if they were fine-tuned on the specific motion blur distribution (generated via `LeviBorodenko/motionblur`) used for GARD training. If baselines were only pre-trained on natural images, the comparison is unfair, as they face a domain shift not accounted for in the evaluation protocol. 

Third, Section 4.2 (`sec/4_method.tex`) defines the Attention Alignment Loss using target maps $\mathbf{A}^*$ derived from ground-truth geometry (point clouds). The manuscript lacks critical discussion on how this dependency impacts real-world deployment where GT is unavailable. No alternative inference strategy or unsupervised alignment mechanism is proposed, creating a gap between the training methodology and practical applicability. These omissions fundamentally weaken the scientific evidence supporting the claim that GARD is robust and deployable.
