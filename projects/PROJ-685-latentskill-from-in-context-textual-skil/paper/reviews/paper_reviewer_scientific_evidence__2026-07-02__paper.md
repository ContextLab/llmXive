---
action_items:
- id: 0561e98a051b
  severity: science
  text: The sensitivity analysis (Appendix app:perturbation) lacks statistical significance
    testing. With N=140/134 episodes per ALFWorld split and N=500 per Search-QA dataset,
    the authors should report confidence intervals or p-values for the observed performance
    gaps between LatentSkill and In-context baselines to rule out variance-driven
    claims.
- id: 19ae3ca0605a
  severity: science
  text: The compositionality claim relies on a single skill pair (Look/Pick) across
    31 episodes (Table tab:compose). This sample size is insufficient to generalize
    the 'composable' property to arbitrary skills. The authors should either expand
    the composition experiments to more skill pairs or temper the claim to 'demonstrated
    on a specific complementary pair'.
- id: 4f09d7c4edb8
  severity: science
  text: The OOD generalization analysis (Section 4.3) uses MDS on 42 total skills
    (8 in-domain + 34 OOD) without reporting statistical measures of cluster separation
    (e.g., silhouette scores or permutation tests). Visual separation in Figure fig:lora_mds
    is suggestive but not rigorous evidence of structured geometry.
artifact_hash: a8058c08d3783326623ffd4fe82cc98eaea95cd3e37911390d531e390197b756
artifact_path: projects/PROJ-685-latentskill-from-in-context-textual-skil/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T17:39:36.622942Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling empirical case for LatentSkill, with robust main results on ALFWorld and Search-QA benchmarks. The performance gains over in-context baselines are substantial and consistent across splits. However, the scientific evidence supporting the specific claims of "structured," "controllable," and "composable" properties requires stronger statistical grounding.

First, the sensitivity analysis in Appendix app:perturbation (Table tab:sensitivity_full_table) reports point estimates for performance under perturbations but omits measures of variance or statistical significance. Given the sample sizes (140/134 episodes for ALFWorld, 500 for Search-QA), the authors should compute 95% confidence intervals or perform paired t-tests (or non-parametric equivalents) to confirm that the observed margins (e.g., +21.4% on ALFWorld seen) are not artifacts of random variance. Without this, the robustness claims remain descriptive rather than statistically validated.

Second, the claim of "composability" is supported by a single experiment involving the Look and Pick skills across 31 episodes (Table tab:compose). While the case studies in Appendix app:case_study provide valuable mechanistic insight, a sample of 31 episodes is too small to generalize the finding that "skills can be composed" as a broad property of the framework. The failure modes of Direct and Text merging are well-documented, but the success of Component Merging on this specific pair does not prove it will hold for arbitrary skill combinations. The authors should either expand the composition experiments to include at least 3-4 distinct skill pairs or explicitly limit the claim to "demonstrated feasibility on complementary skill pairs."

Third, the evidence for "structured" weight space relies heavily on visual inspection of MDS plots (Figure fig:lora_mds). While the clusters appear distinct, the paper lacks quantitative metrics of cluster separation (e.g., silhouette coefficients, Davies-Bouldin index, or permutation tests for cluster significance). The reported cosine similarities (0.982 vs 0.910) are informative but do not account for the high dimensionality of the weight space or the potential for overfitting in the MDS projection. A statistical test confirming that the observed inter-cluster distances are significantly larger than expected by chance would strengthen this claim.

Finally, the injection coefficient analysis (Table tab:scale) shows a clear inverted-U curve, but the optimal $\alpha$ values vary significantly across tasks (e.g., 0.3 for Heat vs 0.8 for Pick2). The paper notes this variation but does not provide a statistical analysis of the stability of these optima across different random seeds or data splits. Reporting the variance of optimal $\alpha$ across multiple runs would clarify whether the "controllable" property is robust or highly sensitive to specific task instances.

Overall, the core performance claims are well-supported, but the auxiliary claims regarding the geometric and compositional properties of the latent space require more rigorous statistical validation to be considered scientifically robust.
