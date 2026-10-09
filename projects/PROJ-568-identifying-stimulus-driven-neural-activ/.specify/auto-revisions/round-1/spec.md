# Revision Specification: Paper Science Revision — PROJ-568-identifying-stimulus-driven-neural-activ round 1

**Generated**: 2026-06-26T14:42:33.164264+00:00
**Kind**: paper_science
**Project**: PROJ-568-identifying-stimulus-driven-neural-activ
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[880aa81144e8] (severity: writing)** The bibliography section in e000 is truncated after ArchEtal07, leaving dozens of in-text citations (e.g., Herc09, MannEtal09a, HaxbEtal11) unsupported. This prevents verification of factual claims.
- **[2fc4b39f848b] (severity: writing)** Specific dataset claims (e.g., n=5023 electrodes from EzzyEtal17) cannot be validated without the full bibliographic entry. Ensure all cited keys have corresponding bibitems.
- **[3404a34fd40c] (severity: science)** No analysis code repository or scripts provided to verify the reproducibility of the methods described (e.g., HTFA, Hyperalignment in Section 2). For a code quality review, artifacts enabling reproducibility from scratch are required.
- **[9b392ba87305] (severity: science)** Complete the truncated bibliography in e000 (ends mid-sentence at 'navigation in'). Provenance requires full citation details for all referenced works.
- **[9841ee07fae6] (severity: science)** Add a Data Availability Statement specifying repositories for datasets cited in figures (e.g., EzzyEtal17, OwenEtal20), including access links or DOIs.
- **[7d8158899362] (severity: science)** Include dataset version numbers and license information for any external data sources referenced in the methodology sections.
- **[604f08a7a58d] (severity: writing)** Add alt text for all figures (e.g., egin{figure}[alt=...] ...) to ensure accessibility compliance for visually impaired readers.
- **[66ffcaec9c16] (severity: writing)** Specify colorblind-safe palette in figure captions or methods (e.g., Viridis, ColorBrewer) for fig:spacetime and fig:electrodes which use multiple colors.
- **[d55b1cdb8553] (severity: writing)** Ensure axis labels and units are present in all multi-panel figures (fig:signals, fig:supereeg); captions mention axes but verification requires visual inspection.
- **[6e7dc8ecfb99] (severity: writing)** Standardize figure widths across all figures (currently varies: 	extwidth, 0.8	extwidth, 0.6	extwidth, 0.5	extwidth) for consistent print legibility.
- **[9897c0f69adf] (severity: writing)** Verify permissions and attribution for all 'adapted from' figures (fig:spacetime, fig:patterns, fig:geometry, fig:tfa, fig:supereeg) per journal requirements.
- **[f3a6ed200192] (severity: writing)** Abstract (e000/e001) lists 9+ acronyms (GLM, MVPA, RSA, etc.) without definition. Define each at first use or move to body text to improve accessibility for non-specialists.
- **[4a7d94632fdb] (severity: writing)** Figure e002 caption mentions 'MNI152 space' without definition. Add a brief parenthetical explanation (e.g., 'standard anatomical coordinate space') for non-neuroimaging readers.
- **[c7295e37d264] (severity: writing)** Section 2 (e002) uses 'procrustean transformation' without simplification. Suggest adding 'geometric alignment' as a plain-language synonym to reduce barrier to entry.
- **[24b56697ed89] (severity: science)** Add explicit statement about IRB approval and informed consent procedures for all cited intracranial EEG datasets. This survey references data from 53 patients (n=5023 electrodes); readers need assurance ethical standards were met.
- **[1e81764f785d] (severity: science)** Include discussion of data privacy and de-identification procedures used in the referenced studies. Patient electrode locations and neural recordings could potentially be re-identified without proper safeguards.
- **[6546bb3d33c8] (severity: science)** Address dual-use considerations for brain activity decoding methods discussed (e.g., neural decoding, stimulus reconstruction). These techniques could have applications beyond cognitive neuroscience.
- **[486bfd9dd1ba] (severity: science)** The manuscript is a methodological survey without primary empirical data. Consequently, the scientific evidence lens cannot evaluate internal sample sizes or controls. Please explicitly clarify in the introduction that this chapter reviews external evidence rather than presenting new experimental results, and discuss the limitations of the cited literature's evidence strength (e.g., sample sizes in referenced iEEG studies).
- **[28a68b6585cd] (severity: writing)** Section 2.1.2 (RSA) omits discussion of multiple-comparisons correction for searchlight analyses. Without FWE or FDR control, reported spatial patterns may reflect false positives.
- **[5b59ba34b623] (severity: writing)** Section 2.1.1 (GLMs) describes the model form but lacks details on link function selection, error distribution assumptions, or residual diagnostics required for valid inference.
- **[c202c8d04032] (severity: writing)** Section 2.2.2 (Gaussian processes) mentions spatial blurring but does not address kernel selection, hyperparameter optimization, or cross-validation procedures essential for reproducibility.
- **[47b1bd8f2681] (severity: writing)** Section 2.2.3 (ISC/ISFC) describes correlation computation but does not specify null models or permutation testing procedures to establish statistical significance against noise.
- **[d8106f3a84ab] (severity: writing)** Resolve document structure: Merge chunks e000, e001, and e002 into a single valid LaTeX file with exactly one \begin{document} and \end{document} marker.
- **[d22e7fdb0475] (severity: writing)** Complete bibliography: The bibliography in e000 is truncated at \bibitem{ArchEtal07}. Ensure all cited keys (e.g., JonaKord17, HaxbEtal11) have corresponding entries.
- **[573df782a2de] (severity: writing)** Standardize caption formatting: Wrap long figure caption lines (e.g., fig:spacetime in e000) to <=80 characters for source hygiene and version control readability.
- **[eb377c1dba76] (severity: writing)** Remove duplicate command definitions: Consolidate \providecommand definitions for \url and \doi which appear redundantly in the preamble and bibliography section.
- **[3d999b435291] (severity: writing)** Correct the typo 'drug-resistent' to 'drug-resistant' in the Summary and concluding remarks section.
- **[206e377a43b8] (severity: writing)** Remove the repeated word 'taken' in the sentence 'taken taken as patients watched' within the Hyperalignment subsection.
- **[dcfa4da0e65b] (severity: writing)** Replace the informal adverb 'incredibly' in the Overview section with a more academic term (e.g., 'particularly' or 'significantly').
- **[779d516a22a7] (severity: writing)** Reduce repetition of the word 'quality' in the Summary section (e.g., 'recording quality', 'quality or fidelity').


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 30 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
