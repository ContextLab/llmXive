# Revision Specification: Paper Science Revision — PROJ-746-the-topological-trouble-with-transformer round 1

**Generated**: 2026-06-26T10:34:58.432437+00:00
**Kind**: paper_science
**Project**: PROJ-746-the-topological-trouble-with-transformer
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[bc63b227fa7c] (severity: writing)** Add missing bibliography entries for cited keys: meng2022locating, Chrisman1992, kaelbling1998planning, baldelli2026, galashov2025, grazzi2025, lin2025forgetting, leviathan2025selective, beltagy2020longformer, oncescu2026, olsson2022context, hochreiter1997long.
- **[5e11edd5679d] (severity: science)** Verify that claims attributed to missing citations (e.g., state tracking failures in multi-turn conversations) are supported by the actual content of the referenced works once added.
- **[4092b6598896] (severity: writing)** Duplicate package imports in preamble: booktabs, array, multirow, and ragged2e are each imported twice (lines ~30 and ~45). Consolidate to single imports for cleaner code.
- **[03ac85faf379] (severity: writing)** Bibliography file has critical syntax errors: 'misc{bae2025,' missing @ symbol (line ~280), and file appears truncated ending with 'doi = "10' without closing brace. Fix before compilation.
- **[ce7df9e4eba5] (severity: writing)** Draft mode enabled with \drafttrue and active todo notes. Disable draft mode and remove all \todo, \marginvn, \inlinevn commands before final submission.
- **[b65f9bf7f0b5] (severity: writing)** Commented-out code blocks should be removed (e.g., \PassOptionsToPackage{natbib}, unused author examples). Clean up for production-ready LaTeX.
- **[e7f81138edbd] (severity: writing)** Correct bibliography schema errors in topological_trouble.bib where entries like 'misc{bae2025' and 'misc{sawyer2025' are missing the leading '@' symbol.
- **[8a3f7b9db429] (severity: writing)** Clarify figure provenance and licensing for adapted figures (e.g., Figure 3) by adding explicit license statements or permission notes.
- **[baf21af70f7b] (severity: writing)** Set \draftfalse or remove draft comments before final submission to ensure artifact integrity.
- **[1bdd14ffe44f] (severity: writing)** Figure 2 (ff_other_models_onerow.pdf) has a commented-out original version in the LaTeX. Verify the final figure is the intended one and remove commented code before submission.
- **[d7de1492be56] (severity: writing)** Figures adapted from external sources (e.g., Fig 4 from rumelhart1986, Fig 3 from lepori2025) need explicit permission statements or license information in captions for arXiv submission.
- **[ccb14f308ce5] (severity: writing)** All schematic figures lack axis labels or scale indicators where applicable. Add visual scale bars or layer/token counts to make depth comparisons quantifiable.
- **[68efffedac78] (severity: writing)** Color choices in Fig 1 (xformer_pic_shaded.pdf) use colored lines/shading for connectivity. Verify these are distinguishable in grayscale print and provide colorblind-safe alternatives.
- **[9a44a8a37422] (severity: writing)** Define 'MAP estimate' at first use in Section 2 (State tracking).
- **[6f0547e7233b] (severity: writing)** Expand 'KV cache' to 'Key-Value cache' in Figure 2 caption.
- **[464f80ae4cca] (severity: writing)** Define 'teacher forcing' and 'attractor dynamics' in Section 3 (Recurrent architectures).
- **[94e4c1fc8959] (severity: writing)** Resolve 'RINS' vs 'RINs' inconsistency in Table 1 and Section 3.
- **[e433ed89f49e] (severity: writing)** Define 'arithmetic intensity' and 'eigenvalue range' in Section 5 (Promising directions).
- **[bc9c5776e472] (severity: science)** Resolve the apparent contradiction between the Abstract (dynamic depth bypasses limit) and Section 3 (depth recurrence does not enable indefinite tracking). Explicitly define 'dynamic depth' vs 'depth recurrence' to ensure logical consistency.
- **[5bd0d7e0ba02] (severity: science)** Clarify the causal mechanism for the 'state shifting upward' claim in Section 3. Distinguish between unrolled graph depth and physical layer depth to support the argument that parallelization, not just depth, limits state tracking.
- **[5f971cefc12f] (severity: writing)** Qualify theoretical claims in Abstract and Intro to distinguish between theoretical bounds and practical limitations.
- **[666fe67e8b90] (severity: science)** Replace anecdotal evidence (Gemini examples) with broader empirical analysis or soften claims about 'fundamental limitations'.
- **[66f14b928960] (severity: writing)** Verify or soften the claim regarding empty taxonomy cells in Section 3.
- **[af5ce98949ff] (severity: writing)** Reframe prescriptive conclusions to recommendations rather than necessities.
- **[2d72f08eb9a3] (severity: science)** Clarify whether claims about model failures are theoretical or empirical. If empirical, provide statistical aggregation or cite specific quantitative studies more rigorously.
- **[7fcc1599a80b] (severity: science)** Address the N=1 nature of the provided model traces (e.g., the '20 questions' example) and discuss alternative explanations like training data distribution.
- **[186f560a3863] (severity: science)** Paper makes claims about model failure rates and performance limitations without systematic statistical testing. Consider adding quantitative analysis with appropriate statistical methods to support empirical claims.
- **[2034beda2b2b] (severity: science)** Citations to empirical work (e.g., lepori2025, li2025) should include specific statistical evidence (effect sizes, confidence intervals) when making quantitative claims about model limitations.
- **[8345f37b31c2] (severity: writing)** Replace informal phrases such as "cop out" (Section 2), "On the flip side" (Section 2), and "a bit weird" (Section 5) with formal academic terminology.
- **[39bdc0cfc908] (severity: writing)** Correct the grammatical error "inputs steps" to "input steps" in Section 3 (near Figure 5).
- **[70d28a551fb8] (severity: writing)** Review the full text for additional colloquialisms (e.g., "came along" in Introduction) to ensure consistent formal tone.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 31 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
