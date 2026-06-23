# Revision Specification: Paper Science Revision — PROJ-627-trisplat-simulation-ready-feed-forward-3 round 2

**Generated**: 2026-06-23T18:43:24.355165+00:00
**Kind**: paper_science
**Project**: PROJ-627-trisplat-simulation-ready-feed-forward-3
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[a6eb651ff5c9] (severity: writing)** Revise the claim that 'no information is lost during export' (Intro/Method) to reflect the measured PSNR degradation (3.21 dB) in Appendix Table 6.
- **[2fcc64b16645] (severity: writing)** Add missing BibTeX entries for cited works (e.g., Held2025Triangle, zhang2025advances) to verify related work claims.
- **[b9f4108224b3] (severity: writing)** Ensure all citation keys in the text match the bibliography file to prevent compilation errors and citation inaccuracies.
- **[345a13e228ef] (severity: science)** Code repository and implementation artifacts are missing from the review package. Please include the full source code (scripts, models, training loops), test suite, and dependency files (requirements.txt or pyproject.toml) to enable assessment of modularity, test coverage, and reproducibility.
- **[d5c03f9bfd48] (severity: writing)** Add a Data Availability Statement specifying dataset licenses (RE10K/DL3DV/ScanNet) and compliance.
- **[33e901b1b3fe] (severity: writing)** Provide a stable code repository URL with a specific commit hash and software license (e.g., MIT/Apache).
- **[8c0472f6947c] (severity: writing)** Archive the project page link (lhmd.top/trisplat) with a DOI to prevent link rot.
- **[8d8a7a0d12ff] (severity: writing)** Convert figures/teaser.png to vector format (.pdf/.eps) for print quality.
- **[4f102a8745d9] (severity: writing)** Move main_dl3dv_mesh_render.pdf and main_dl3dv_textured_mesh.pdf to sections/04_experiments.tex.
- **[9a5a094f8f68] (severity: writing)** Ensure axis labels are present on the pipeline2.pdf bubble chart, not just in caption.
- **[e67f2b315feb] (severity: writing)** Add sub-figure labels (a, b, c) to grouped appendix figures.
- **[df499ee257ad] (severity: writing)** Define acronyms TSDF, SE(3), SO(3), and LPIPS at first use in the main text to ensure accessibility for non-specialist readers.
- **[c599385ccc89] (severity: writing)** Replace dense jargon terms like 'post-hoc', 'gauge ambiguity', and 'latent variable' with plainer alternatives (e.g., 'subsequent', 'coordinate ambiguity', 'internal representation').
- **[1c17a6309010] (severity: writing)** Section 3.4 claims 'trivial' mesh extraction without post-processing, yet describes discarding low-opacity triangles, correcting winding order, and merging duplicate vertices. These ARE post-processing steps. Clarify whether 'no post-processing' means 'no per-scene optimization' or truly no processing, to avoid logical tension between abstract claims and method description.
- **[789932f5a020] (severity: writing)** Appendix Table 6 shows TriSplat has -3.21 PSNR degradation from primitive to mesh rendering. If rendering primitives ARE the exported mesh (core claim), why does degradation exist? Either explain the source of this gap (e.g., opacity thresholding, vertex merging artifacts) or clarify what 'no information loss' means quantitatively.
- **[5de6c512bb3f] (severity: science)** Training objective Eq. 11 includes L_normal that directly supervises against monocular teacher normals throughout training, not just during bootstrap phase. This creates logical tension with Section 3.2's claim that the model 'relies entirely on its own geometry' after release phase. Clarify whether teacher supervision persists and how this affects the self-contained geometry claim.
- **[b578d806b863] (severity: science)** Simulation demonstrations (Appendix 6) show qualitative physics results (ball drop, locomotion) but provide no quantitative metrics on collision accuracy, surface normal consistency for contact, or simulation stability. For a 'simulation-ready' claim, this evidence is insufficient to support the causal link between mesh quality and downstream physics utility.
- **[d0af52db9622] (severity: writing)** Abstract claims 'without any post-processing' (line 45) but Sec 3.4 describes vertex merging and winding correction. This is post-processing; temper the claim to 'minimal post-processing'.
- **[ddbc5dab6ad7] (severity: science)** Simulation readiness is asserted via visual demos (Appendix 5.5) but lacks quantitative physics benchmarks (e.g., collision stability, manifoldness). Add limitations regarding watertightness requirements.
- **[a0a7d8d9a788] (severity: science)** Zero-shot simulation claims (ScanNet) rely on depth/normal metrics (Table 4) not simulation metrics. Clarify that simulation readiness on ScanNet is unverified beyond geometric proxies.
- **[37fccf840fd2] (severity: writing)** Add a statement in Section 4.1 (Datasets) confirming adherence to dataset licenses and privacy protocols, specifically regarding face blurring or consent for YouTube-sourced RealEstate10K data.
- **[618e4632f8f7] (severity: writing)** Include a brief discussion on potential dual-use risks (e.g., unauthorized mapping of private infrastructure) and responsible use guidelines in the Conclusion or an Ethics Statement.
- **[3be20a063835] (severity: science)** Provide quantitative metrics for simulation utility (e.g., collision detection success rate, grasp success) to substantiate the 'simulation-ready' central claim, as current evidence in Appendix 6 is purely qualitative.
- **[c694d97310e5] (severity: science)** Report mean ± standard deviation for all quantitative metrics in Tables 1-4 to assess result stability across scene samples.
- **[58aacf9b38ec] (severity: science)** Conduct formal hypothesis testing (e.g., paired t-tests) comparing TriSplat against baselines to validate claims of "consistent outperformance."
- **[3ed67aa4ae20] (severity: science)** Include per-scene variance or confidence intervals for the zero-shot ScanNet evaluation (Table 3) to demonstrate generalization stability.
- **[93b7cc41f08c] (severity: writing)** Replace custom \boldstart command with standard \subsubsection or \paragraph commands to ensure semantic heading hierarchy and TOC generation.
- **[54ef4b4bf955] (severity: writing)** Standardize BibTeX booktitle field formatting in reference.bib (remove extra spaces before values).
- **[180a0d3b12e6] (severity: writing)** Review \resizebox usage on tables in Appendix; prefer adjusting column widths or font size to maintain readability.
- **[bfa771bd000f] (severity: writing)** Remove duplicate figure labels in sections/04_experiments.tex (e.g., fig:nvs_qual_mesh and fig:nvs_qual_mesh_re10k defined on the same figure block).
- **[d39e4f457de6] (severity: writing)** Typo in section 04_experiments.tex, line ~145: 'rende ring' should be 'rendering'. Fix this typo in the phrase 'primary rende ring metric'.
- **[9d1892c18071] (severity: writing)** Section 02_related_work.tex has several very dense paragraphs (e.g., first paragraph of 'Splatting-Based Scene Representations'). Consider breaking these into 2-3 shorter paragraphs for improved readability.
- **[48ef1e77a6a0] (severity: writing)** Some sentences throughout the manuscript are quite long and complex (e.g., introduction line ~25, related work line ~10). Consider splitting for better flow without losing technical precision.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 33 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
