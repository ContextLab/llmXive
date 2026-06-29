# Revision Specification: Paper Science Revision — PROJ-597-https-arxiv-org-abs-2605-11739 round 1

**Generated**: 2026-06-29T03:38:28.846418+00:00
**Kind**: paper_science
**Project**: PROJ-597-https-arxiv-org-abs-2605-11739
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[8c96d28125c0] (severity: science)** Abstract claims OPD achieves 3x training acceleration over RL, but Section 4 attributes 3x speedup to EffOPD vs. Vanilla OPD. Correct this conflation.
- **[dc74a124d6ac] (severity: writing)** Citation `item_f3c74b8f1cad43ed869604b318d58703` in Section 3.1 is a placeholder ID, not a valid bibliographic entry. Replace with a proper source.
- **[a334054b7e1c] (severity: writing)** Appendix contains a geometry problem tcolorbox (e001, e003) unrelated to the paper's content. Remove this irrelevant artifact.
- **[97e49a89b8fa] (severity: science)** Training command in Appendix (tcolorbox py1, line ~380) has omitted config lines preventing full reproducibility. All hyperparameters must be visible.
- **[b40f636b24de] (severity: science)** No dependency specifications (requirements.txt, environment.yml) visible in paper or supplementary materials. Hardware configuration incomplete.
- **[bfcb79bed61f] (severity: science)** No test suite or validation scripts visible. Cannot verify reproducibility of reported results without access to evaluation code.
- **[af8a80d28daf] (severity: writing)** Resolve inconsistency between anonymous code link in Abstract (e000) and GitHub link in metadata summary. Provide a permanent, versioned repository URL.
- **[1ed3e80a14a3] (severity: writing)** Specify dataset versions and licenses for all external data (e.g., AIME24/25/26, DeepMath-103K, MATH500) to ensure provenance and compliance.
- **[b5fbabe64c67] (severity: writing)** Document the provenance and availability of the 50-sample validation set D_v used in EffOPD (Section 5).
- **[6851d0116f74] (severity: writing)** In Section 3.2 (e002), the text references 'Figure~\ref{fig4} (b)' for tail subspace analysis, but Figure 3 (b) is labeled 'Bottom-k% subspace'. Correct the reference to match the caption content.
- **[d9dce0426009] (severity: writing)** The appendix contains 12+ nearly identical t-SNE visualization figures (e.g., tsne_grid_mlp_down_proj.pdf). Consolidate these into a single composite figure or table to reduce clutter.
- **[7177960649d5] (severity: writing)** Add descriptive alt text or detailed captions for all figures to ensure accessibility for screen readers, particularly for the t-SNE plots where visual trends are key.
- **[52791dc3ba22] (severity: writing)** Define acronyms SVD, t-SNE, EVR, and RLVR at first use in the main text or appendix.
- **[0e1ed5037bae] (severity: writing)** Expand 'MLP', 'KL', and 'RL' to full terms (Multi-Layer Perceptron, Kullback-Leibler, Reinforcement Learning) upon first occurrence in the Introduction.
- **[750d48fe8594] (severity: writing)** Clarify coined terms like 'Functional Redundancy Avoidance' and 'Early Low-Rank Lock-in' with plain-language summaries to aid non-specialist readers.
- **[14c6cfa6748a] (severity: science)** Clarify the assumptions underlying the linearized OPD dynamics (Section A Linearized View). Specifically, provide empirical evidence that the residual r_c is indeed low‑rank/sparse and that the spectral gap condition holds for the models studied.
- **[2ec502c637fd] (severity: science)** Add a statistical significance analysis (e.g., confidence intervals or multiple random seeds) for the reported speed‑up and accuracy gains of EffOPD to ensure the observed improvements are not due to variance.
- **[6c5801b50474] (severity: writing)** Explain how the validation set size (50 samples) was chosen and demonstrate that the extrapolation does not overfit to this tiny set, perhaps by reporting results with different validation set sizes or by cross‑validation.
- **[f948e63ac0b3] (severity: writing)** Reframe 'foresight' terminology in Abstract and Intro to 'early stabilization' to avoid anthropomorphic overreach not fully supported by local linearization theory.
- **[b6ca6c6a1924] (severity: writing)** Correct the claim 'no hyper-parameter tuning' in Abstract; EffOPD requires validation set selection and search over extrapolation factor k.
- **[e4eef417afa8] (severity: science)** Add error bars or statistical significance tests for performance comparisons (Fig 5) as admitted in Checklist Item 7.
- **[96b8465cc357] (severity: writing)** Expand the Impact Statement (Section 'Impact Statement', e002) to explicitly discuss dual-use risks of accelerated reasoning capabilities (e.g., faster iteration on harmful content generation) and recommend pairing efficiency gains with safety alignment protocols.
- **[16c3d18ee5d9] (severity: science)** Report results over multiple random seeds with error bars for main performance claims (Fig. 5, Table 1) to establish statistical significance.
- **[09c98bccd60a] (severity: science)** Justify the 50-sample validation set size for EffOPD selection; provide sensitivity analysis to ensure robustness against overfitting.
- **[51318bbeb955] (severity: science)** Clarify causal vs. correlational nature of 'foresight' mechanism; consider ablation disrupting low-rank structure to test necessity.
- **[afcb319d7bb3] (severity: science)** Re-run main experiments with multiple random seeds (e.g., 3-5) and report mean ± standard deviation for all quantitative metrics (Table 1, Figure 5) to establish statistical significance.
- **[0e05b4474280] (severity: science)** Justify the validation set size (50 samples) for EffOPD step selection with a power analysis or increase the size to reduce variance in decision-making.
- **[a08a92d9a9b6] (severity: science)** Apply multiple-comparison corrections (e.g., Bonferroni) when claiming consistent superiority across model scales and tasks, and report p-values for key comparisons.
- **[9f61e08ac2d5] (severity: writing)** Text Formatting Review This review focuses exclusively on text formatting, heading hierarchy, list/table formatting, citation/cross-reference style, line wrapping, LaTeX hygiene, and figure-caption placement. Heading Hierarchy Issues The document uses \section, \subsection, and \paragraph commands appropriately in structure, but there are critical duplicate label conflicts. The labels \label{section2} and \label{section3} appear in both the main text (e000) and appendix (e002), which will cause
- **[7e1f826bfd08] (severity: writing)** Revise the title to remove redundant phrasing ('Unveiling the Unlocking'). Suggest 'Unveiling the Efficiency' or 'Unlocking the Efficiency'.
- **[c9b02b18c776] (severity: writing)** Convert sentence fragments in Section 4 (Main Results) and Section 9 (Experimental Setup) into complete sentences to improve flow.
- **[33b4c0e67f5a] (severity: writing)** Standardize figure and table referencing style (e.g., 'Figure~ef{fig1}(a)' vs 'Fig.~ef{fig1}a') throughout the document.
- **[666b65308c6d] (severity: writing)** Fix the typo in the label '\label{resoning chains}' to '\label{reasoning_chains}' to prevent broken links.
- **[8313723f18de] (severity: writing)** Resolve duplicate section definitions (e.g., '\section{Conclusion}' appears in multiple chunks) to ensure logical document structure.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 34 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
