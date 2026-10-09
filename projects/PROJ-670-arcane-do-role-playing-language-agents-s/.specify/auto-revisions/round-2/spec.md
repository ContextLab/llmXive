# Revision Specification: Paper Science Revision — PROJ-670-arcane-do-role-playing-language-agents-s round 2

**Generated**: 2026-06-28T10:11:34.673134+00:00
**Kind**: paper_science
**Project**: PROJ-670-arcane-do-role-playing-language-agents-s
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[9ce1fe796de0] (severity: writing)** Several in-text citations (e.g., \citep{character_ai}, \citep{park2023GenerativeAgent}, \citep{shao-etal-2023-characterllm}, \citep{wang-etal-2024-rolellm}, \citep{Markel2023GPTeach}) are not present in the bibliography. Add the missing bibliography entries or remove the citations to ensure every reference is verifiable.
- **[3e12cfe418ff] (severity: science)** The claim that "Arc is the only mode that supplies the per-chapter trajectory PTF scores" should be double-checked against the description of the evaluation protocol to confirm no other mode inadvertently provides trajectory information.
- **[8ecebd03863b] (severity: writing)** Verify that all quantitative statements (e.g., performance numbers in Table 1 and Table 2) exactly match the reported results; any rounding inconsistencies should be clarified.
- **[b7c5dc08d88b] (severity: writing)** Add specific library versions (e.g., vLLM, transformers) to Appendix: Training Setup for reproducibility.
- **[57accbcf7fdf] (severity: writing)** Specify exact data paths and JSON schemas for the ArcANE dataset in Appendix: Datapoint information.
- **[0b3b730a64fc] (severity: writing)** Include a description of testing infrastructure (unit/integration tests) for the pipeline stages.
- **[59f4dd34dd71] (severity: writing)** Ensure released code follows the modular structure described (Arc Construction, Probe Generation, Training).
- **[574d87415a88] (severity: science)** Clarify license compatibility for Harry Potter-derived probes under CC-BY-4.0, as the source text is copyrighted (Appendix \S\ref{app:datapoint}).
- **[583a8599bb91] (severity: writing)** Specify a dataset version number (e.g., v1.0) to ensure reproducibility of the benchmark split and schema.
- **[31fb296e3216] (severity: writing)** Report the validation drop rate (number of probes marked 'unavailable' vs. total generated) to assess data quality filtering rigor (Appendix \S\ref{app:probe-details}).
- **[234e6fe063d0] (severity: writing)** Verify the arXiv ID date (2606.05553 implies June 2026) to ensure provenance links are valid and not simulated.
- **[3c4706f01a9a] (severity: writing)** Correct the typo 'LLm' to 'LLM' in the caption of Figure 7 (fig:annotation_2) in the Appendix.
- **[d3b385a92fd4] (severity: writing)** Expand the caption of Figure 2 (fig:pipeline) to explicitly describe the top (arc construction) and bottom (probe generation) stages for better self-containment.
- **[98c8cc21798d] (severity: writing)** Ensure all figure files (PDF/JPEG) are high-resolution enough for print legibility, particularly for text-heavy screenshots like Figures 5, 6, and 7.
- **[ef8a61df94c5] (severity: writing)** Define acronyms like RAG, SFT, DPO, and LoRA at first use in the main text rather than relying on Appendix references for core methodology.
- **[5fb4fba69ff1] (severity: writing)** Simplify or briefly gloss psychological terms (e.g., 'Agency-Communion', 'McAdams' Layer') to ensure accessibility for non-specialist NLP readers.
- **[2bde94f8a90b] (severity: writing)** Reduce reliance on custom validator names (Q-Voice, Q-PhaseFit) in the main text; consider descriptive names or a summary table.
- **[84c61431242b] (severity: science)** Revise Abstract and Section 5.3 claims regarding 'other role-playing model families'. Appendix Table tab:main_results_added shows HER-32B performs better with RAG than Arc on Overall (47.0 vs 46.4) and In-Scenario metrics, contradicting the claim that the Arc pattern carries over universally.
- **[1ce980d5b523] (severity: writing)** Qualify the Conclusion's statement about low-popularity novels. Section 3.3 labels this slice 'unvalidated' (no human annotation), yet the Conclusion presents it as a robust carry-over of the benchmark's success without this caveat.
- **[c6dd9fd9349e] (severity: writing)** Correct the numerical range in the Conclusion. The text claims a lift of '+4.1 to +15.3', but Appendix Table tab:main_results_extra3 shows ArcANE-32B achieves a lift of 16.2 (65.5 - 49.3) on the low-popularity slice.
- **[7c1ba8b3a6cb] (severity: writing)** The paper acknowledges dual-use risks (impersonation) only in Limitations. Expand this discussion in the main text to include potential mitigation strategies for downstream users (e.g., watermarking, disclosure requirements).
- **[486d8b04cd00] (severity: science)** The dataset includes probes derived from Harry Potter (copyrighted). Releasing these under CC-BY-4.0 may infringe copyright. Clarify the legal basis for public release or restrict access to the copyrighted subset.
- **[d50b01bd0e0d] (severity: writing)** Appendix mentions one human study was 'non-compensated'. Ensure this aligns with institutional IRB/ethics guidelines regarding research labor, even for colleagues.
- **[a4d2e1dfbe48] (severity: science)** Report statistical significance (p-values or confidence intervals) for main results in Table 2 to substantiate claims of superiority.
- **[cd4c71bc28f8] (severity: science)** Clarify the extent of human validation on probe reference responses (gt_action, gt_thought), not just Character Arcs.
- **[cd135143d9e1] (severity: science)** Provide independent human evaluation of model responses to validate the LLM judge's absolute accuracy, beyond anchored calibration.
- **[12d77dc838fd] (severity: science)** Add statistical significance testing (e.g., paired t-tests or Wilcoxon) for the main results in Table 1 to substantiate claims of superiority over baselines.
- **[78218a49737d] (severity: science)** Report confidence intervals or standard deviations for all mean scores to quantify variance in LLM generation and judging.
- **[58d3791b1f50] (severity: science)** Address multiple comparisons correction (e.g., Bonferroni or FDR) given the 36 model-mode combinations tested.
- **[cbad1bf6dbc7] (severity: writing)** The LaTeX source generally follows good formatting conventions: headings use \section with proper labels, figures include \centering, \includegraphics, a caption placed before the \label, and appropriate placement specifiers. Tables are defined within table* environments, use booktabs rules, and have captions preceding labels, which is correct. Citations consistently use the \citep command, and the bibliography is included via \bibliography{custom}. However, the preamble contains several redunda
- **[af33c2f682b9] (severity: writing)** Replace informal phrasing 'tops every other context strategy' in Abstract with 'outperforms' for formal tone.
- **[a76c3b5dddcf] (severity: writing)** Correct LaTeX typo 'Sef{sec:additional}' to '\Sef{sec:additional}' or 'Section ef{sec:additional}' in Section 5.2.
- **[56bffc0ae126] (severity: writing)** Rephrase convoluted sentence in Section 6.2 regarding Hagrid to improve clarity and flow.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 33 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
