---
action_items:
- id: 486bfd9dd1ba
  severity: science
  text: The manuscript is a methodological survey without primary empirical data.
    Consequently, the scientific evidence lens cannot evaluate internal sample sizes
    or controls. Please explicitly clarify in the introduction that this chapter reviews
    external evidence rather than presenting new experimental results, and discuss
    the limitations of the cited literature's evidence strength (e.g., sample sizes
    in referenced iEEG studies).
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T13:25:05.118682Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This manuscript functions as a methodological survey chapter rather than an empirical study. Consequently, the `scientific_evidence` lens cannot evaluate internal sample sizes, controls, or effect sizes, as no new data is presented. Per the review constraints, this state warrants a `minor_revision` to address the applicability of the evidence lens.

Specific concerns regarding the strength of claims made about the evidence landscape include:

1.  **Methodological Comparisons:** In Section 2.1.2 (e002), the text claims "RSA can sometimes be a more sensitive way of identifying stimulus-driven neural patterns" compared to MVPA. While this is a valid methodological point, the text does not quantify the evidence base for this claim (e.g., citing benchmarking studies or meta-analyses that report effect sizes for RSA vs. MVPA). The review should better qualify the empirical support for such comparative claims to avoid overstating the robustness of these methods.

2.  **Coverage Claims:** Section 1.1.2 (e000) states intracranial recordings are "ideally suited to studying stimulus-driven neural activity patterns," citing Figure 1. While Figure 1 illustrates resolution, it does not provide evidence on the *reliability* or *replication* of findings using these methods across the 53 patients mentioned in Figure 3. The text should acknowledge that high resolution does not guarantee robust evidence if sample sizes (n=53 patients) are insufficient for generalizable claims about specific cognitive functions.

3.  **Evidence Limitations:** The chapter summarizes approaches (GLMs, Gaussian processes, etc.) but does not critically evaluate the quality of evidence supporting each. For instance, Section 2.2.1 describes hierarchical matrix factorization but does not mention potential overfitting risks or validation requirements (e.g., cross-validation performance) that would support the scientific validity of the resulting factors.

To address these issues, the authors should add a discussion on the limitations of the evidence base for the methods described, specifically highlighting sample size constraints in the cited iEEG literature and the need for replication in across-patient models.
