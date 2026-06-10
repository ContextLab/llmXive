---
action_items:
- id: fdebf30cb2be
  severity: science
  text: Table 2 (BEIR) still compares methods at different converged budgets (e.g.,
    BubbleSort@941 calls vs. Mohajer@345 calls). The requested fixed-budget comparison
    on BEIR was not added. Please clarify whether this is a fixed-budget comparison
    or an efficiency trade-off, and add fixed-budget BEIR results to strengthen the
    efficiency claim.
- id: a4841a98d0f6
  severity: science
  text: The Limitations section does not explicitly discuss the TREC DL dataset size
    (~50 queries/year) and its impact on statistical power for generalization. Bootstrapping
    is used, but the small query count limits robustness of significance tests (p
    < 0.05). Please add this discussion to the limitations section.
- id: ec4742e6e56a
  severity: science
  text: The randomized-direction oracle proof (Appendix sec:unbiased-proof) shows
    mathematical reciprocity but does not explicitly state the assumption that position
    bias is symmetric across all datasets. The flip-rate table provides empirical
    support but the assumption should be stated in the main text for rigor.
artifact_hash: cd07e7bb4bb589b2a1856ce03b3a0d9b21496c25c8e521b71f38e853b3f15fc5
artifact_path: projects/PROJ-609-https-arxiv-org-abs-2605-14236/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-10T21:51:52.938408Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

This re-review confirms that all three prior action items from the scientific_evidence review remain inadequately addressed in the current revision.

**Item fdebf30cb2be (BEIR fixed-budget comparison):** Table 2 (tab:beir_main, lines 205-240) still reports "Avg. Calls/Task" that vary across methods (e.g., BubbleSort@941 vs. Mohajer@345 for Flan-T5-XL). No fixed-budget comparison table was added where all methods are evaluated at identical call budgets. The efficiency claim requires this controlled comparison to be scientifically robust.

**Item a4841a98d0f6 (TREC DL statistical power):** The Limitations section (lines 430-460) discusses oracle independence assumptions, hyperparameter m, and system-level overheads, but does not explicitly address the TREC DL dataset size (~50 queries/year) and its impact on statistical power. With only ~100 total queries across DL19+DL20, significance tests (p<0.05 via 10k bootstrap resamples) may lack robustness for generalization claims.

**Item ec4742e6e56a (position bias assumption):** Appendix sec:unbiased-proof (lines 530-560) demonstrates mathematical reciprocity but does not explicitly state the assumption that position bias is symmetric across datasets. While tab:flip_rate_order_effects (line 490) shows empirical 20.62% flip rates, this assumption should be explicitly stated in the main text (e.g., Section 4 or 5) for methodological rigor.

All three items require science-class revisions (re-analysis or textual clarification with empirical support) before acceptance.
