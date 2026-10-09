# Revision Specification: Paper Science Revision — PROJ-686-on-the-geometry-of-on-policy-distillatio round 1

**Generated**: 2026-06-13T01:03:19.003136+00:00
**Kind**: paper_science
**Project**: PROJ-686-on-the-geometry-of-on-policy-distillatio
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[d10639f35211] (severity: writing)** Remove commented-out LaTeX blocks and inline reviewer comments (e.g., 'Yi: ...') from source files to ensure a clean final submission.
- **[62611a7b0618] (severity: writing)** Table 1 lists 'Published reference points' (e.g., Klear-Reasoner, Polaris) without bibliographic citations. Add references to the original releases or papers for these checkpoints to support the claim of their existence and properties.
- **[ad829f59d1cd] (severity: writing)** Section app:experimental-details cites `olmo2025olmo3` for 'Dolci-Think SFT data'. Verify if this data is explicitly described in the Olmo 3 paper or if a separate dataset citation is required to support the data provenance claim.
- **[013b022b124e] (severity: writing)** LiveCodeBench v5 is cited using the 2024 Jain et al. paper. If v5 is a newer version not covered by the 2024 publication, update the citation or clarify the version relationship to ensure accuracy.
- **[58d5e7e82bc5] (severity: writing)** Release the actual training and analysis code (e.g., GitHub link or archive). The paper mentions AI-drafted scripts in Appendix 'AI Usage' but provides no repository URL or code snippets for the diagnostic calculations.
- **[50fcf953a81b] (severity: writing)** Provide a dependency specification (requirements.txt or environment.yml) for the experimental setup. Appendix Tables list hyperparameters but not software versions (e.g., PyTorch, transformers, sglang).
- **[331361cc4ac7] (severity: writing)** Include unit tests or a verification script for the parameter-space diagnostics (stable rank, spectral drift) to ensure reproducibility of the geometric claims.
- **[03ab5ad3f665] (severity: writing)** Explicitly list the specific open-source licenses (e.g., MIT, Apache 2.0) for all external datasets and checkpoints mentioned in Appendix Artifact Use, rather than stating only that terms were checked.
- **[6f4d1eef397a] (severity: writing)** Provide a data schema or manifest for the processed analysis artifacts (e.g., the weight delta matrices and checkpoint hashes) to enable independent verification of the parameter-space diagnostics.
- **[5ccfa868a226] (severity: writing)** Replace unstable external links (e.g., the Notion URL for DeepCoder in bibliography) with persistent identifiers (DOI or arXiv ID) to mitigate link rot risks.
- **[672e0f8ae35a] (severity: writing)** Replace 'fig:placeholder' label with a descriptive identifier in sections/01_introduction.tex.
- **[4578664fa273] (severity: writing)** Resolve the undefined axis label 'k' noted in the commented section of sections/04_opd_pnt_framework.tex.
- **[368ef2bb1ca2] (severity: writing)** Convert figures/k16_projection_percent.png to vector PDF to ensure print legibility.
- **[7d7333da2409] (severity: writing)** Define 'ULP' (Unit in the Last Place) in Appendix A or main text; it is computer science jargon not defined for general ML readers.
- **[1a5e2647e412] (severity: writing)** Provide plain-language glosses for coined terms 'relaxed off-principal regime' and 'subspace locking' upon first introduction in Abstract and Introduction.
- **[d08489ab6ad0] (severity: writing)** Clarify 'Hill tail estimator' in Section 5.1 with a brief intuitive explanation, as it is a niche statistical term.
- **[7513e4dc4396] (severity: writing)** Consider replacing 'bf16-aware update sparsity' with 'low-precision visible update sparsity' or similar for clarity.
- **[8f12e175148a] (severity: writing)** Clarify the 'KL loss: Disabled' setting in Table 3 (Appendix) relative to the KL-based objective in Appendix A. The Three-Gate theory relies on a 'distributional anchor' (Gate I), but the table implies no KL regularization. Explicitly state that the distillation KL is the anchor and the disabled loss refers to reference-policy regularization to avoid confusion about the mechanistic explanation.
- **[da510cff51d8] (severity: writing)** Clarify the Abstract and Introduction to distinguish between static intermediate positioning (supported by Table 1) and distinct trajectory dynamics (supported by Section 5). Current phrasing 'not merely an intermediate point' risks implying static metrics are also distinct.
- **[784177c596be] (severity: writing)** Soften Section 6.2 mechanistic claims. Change 'explaining why objective mixing... breaks' to 'suggesting why' to align with the Limitations disclaimer that these are not 'complete causal or formal theories'.
- **[4b53fc4d6865] (severity: writing)** Reinforce generalization boundaries in the Discussion. While Limitations note variability across families, the Discussion claim that geometry-aware control 'may make OPD more... transferable' should explicitly reference the reasoning-task constraint to prevent overgeneralization.
- **[e84d8051fe81] (severity: science)** Report variance for key diagnostic metrics in Figures 1-3 and Table 1 to establish statistical robustness beyond single-run observations.
- **[fe1837d45036] (severity: science)** Address the initialization confound in Section 4 where SFT updates are measured from pretrained Base while OPD and RLVR are from the SFT anchor.
- **[0a06c3b84a07] (severity: science)** Provide sensitivity analysis for the rank-16 projection across different ranks to rule out cherry-picking the bottleneck dimension.
- **[12e9b29593d1] (severity: science)** Add error bars or confidence intervals to trajectory plots (e.g., fig:intrinsic-metrics) to quantify variance across seeds.
- **[49d0eb0751d2] (severity: science)** Report statistical significance (p-values or CIs) for performance comparisons in the rank-16 projection experiment.
- **[a41a42839c24] (severity: science)** Clarify whether main results are averaged over multiple seeds and justify the bf16 threshold eta=10^-3.
- **[5691f1475b2c] (severity: writing)** Remove commented-out code blocks in sections/01_introduction.tex lines 28-55 and sections/05_update_geometry.tex lines 1-130 to ensure source cleanliness.
- **[666af2f9e9e4] (severity: writing)** Standardize citation spacing throughout the manuscript using non-breaking space before cite commands consistently.
- **[9774f6d5ee37] (severity: writing)** Fix inconsistent whitespace before cross-reference commands in sections/appendix.tex line 31.
- **[00aaa95aba29] (severity: writing)** Remove commented-out draft text blocks from sections/01_introduction.tex and sections/05_update_geometry.tex to ensure a clean submission.
- **[e6323155f4ab] (severity: writing)** Delete reviewer notes left in comments, specifically in tables/sparsity.tex and sections/04_opd_pnt_framework.tex.
- **[f325fde11f34] (severity: writing)** Fix double spacing issues, such as 'with a  bias toward' in sections/04_opd_pnt_framework.tex.
- **[3da0e12df799] (severity: writing)** Correct LaTeX reference spacing (e.g., 'Figure ~ef' should be 'Figure~ef') in sections/05_update_geometry.tex.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 34 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
