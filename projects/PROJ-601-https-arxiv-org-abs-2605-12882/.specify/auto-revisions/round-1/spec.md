# Revision Specification: Paper Science Revision — PROJ-601-https-arxiv-org-abs-2605-12882 round 1

**Generated**: 2026-06-12T07:36:53.304544+00:00
**Kind**: paper_science
**Project**: PROJ-601-https-arxiv-org-abs-2605-12882
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[2dc8f3ea432c] (severity: science)** Increase human verification of ground truth annotations or provide statistical justification for the current 200-sample expert review covering 1897 questions.
- **[a15e9baee511] (severity: science)** Standardize input processing (resolution, API access) across all evaluated models to ensure fair comparison.
- **[10b73396c04c] (severity: science)** Model version names (e.g., GPT-5.4, Gemini-3.1-Pro-Preview, Qwen3-VL-235B-A22B) appear to reference non-existent or future versions. Verify all model names against official releases or clarify these are preview/internal versions. This affects the reproducibility and credibility of experimental results.
- **[3b835870367c] (severity: writing)** Multiple citations reference papers from 2025-2026 (e.g., keer2026med, zhao2026retrieval, wang2026mineru2, zhang2026docdancer). While arXiv preprints may be upcoming, verify these papers actually exist or are in press. At minimum, clarify their status (preprint, submitted, in press).
- **[d4814b1f7c35] (severity: science)** Section 4.1 claims SAA = 1_{(Ans. ≥ 4 ∧ (Rel. ≥ 4 ∨ Rec.  ≥ 0.6))}. However, Table 1 shows Rel. and Ans. scores normalized to 0-100  scale (multiplied by 20). The metric definition should be consistent with the actual scoring used in experiments.
- **[a7ba7106d417] (severity: writing)** Code repository not accessible for review. Paper references https://github.com/opendatalab/CiteVQA but implementation code is not provided in review inputs. Cannot evaluate reproducibility, modularity, test coverage, or dependency hygiene without actual source code.
- **[9ae5cf692d02] (severity: writing)** Appendix should include a `requirements.txt` or `environment.yml` file listing all dependencies (MinerU2.5, MLLM APIs, evaluation frameworks) with version pins for reproducibility.
- **[a3e9c2155deb] (severity: writing)** Pipeline scripts described in Section 3 lack code-level documentation. Consider adding a `scripts/` directory structure summary (e.g., `data_collection.py`, `qa_generation.py`, `evaluation.py`) with docstrings in the appendix.
- **[2a01755a5ff8] (severity: science)** Clarify the licensing status of the 711 source PDFs beyond Common Crawl Terms. The current takedown policy (Appendix A.1) is insufficient for reproducible data distribution; specify per-document licenses or public domain status.
- **[25850023f882] (severity: writing)** Add a dataset version number (e.g., v1.0) to the repository and manuscript. The lack of versioning (Abstract, GitHub link) prevents exact replication of the 1,897-question benchmark.
- **[6929fb462e42] (severity: science)** Document the exact versions of proprietary models used in the annotation pipeline (e.g., Gemini-3.1-Pro-Preview, Section 3.2). Reliance on 'Preview' models risks data provenance if these versions are deprecated.
- **[24fa5131e33f] (severity: writing)** Provide a formal schema file (e.g., JSON Schema) for the evidence package format described in Appendix B.1. Textual descriptions alone are prone to parsing ambiguities.
- **[0d9e8bf5776b] (severity: writing)** Figure 1c (Performance) overlaps significantly with Table 1 (Main Results). Consider removing Fig 1c or replacing it with a visualization that highlights the 'Attribution Hallucination' gap (Ans. vs SAA) specifically, rather than repeating the full table data.
- **[f5164afe9b85] (severity: writing)** Radar charts in Fig 5 (citevqa_ability_radar.pdf) and Appendix Fig (citevqa_domain_radar.pdf) are difficult to read with multiple models. Suggest switching to grouped bar charts or heatmaps for better comparison of SAA scores across question types.
- **[50c101f5c8a7] (severity: writing)** Figure 3 (pdf_statistics.pdf) and Figure 4 (question_statistics.pdf) lack explicit axis labels for units (e.g., 'Count', '%', 'Pages'). Ensure all axes are clearly labeled for print legibility.
- **[6745a71357aa] (severity: writing)** Case study figures (Simple_Case.pdf, Case_Study1.pdf, Case_Study2.pdf) have small text in crops. Verify legibility at standard print scale (e.g., 10pt font equivalent). Add arrows or bounding boxes to explicitly highlight cited regions.
- **[00df9bc44ba8] (severity: writing)** Files 'shlab.png' and 'OpenDataLab_blue_no_words.pdf' are listed in the figures directory but not referenced in the LaTeX source. Remove unused assets to reduce repository clutter.
- **[5ea0d86cd128] (severity: writing)** Caption for Figure 7 (Simple_Case.pdf) is generic ('A Typical Example.'). Expand to describe the specific failure mode illustrated (e.g., 'Qwen3-VL-235B answers correctly but cites blank regions').
- **[07b57ce034ee] (severity: writing)** Define all acronyms at first use (IoU, RAG, SFT, QA). Currently used without definition in Section 4.1 and Appendix (e.g., 'IoU@0.5', 'SFT training', 'QA pairs').
- **[f22368cde61f] (severity: writing)** Replace dense jargon in evaluation metrics section (Section 4.1). Terms like 'Traceability Metrics,' 'element-level bounding-box citations,' and 'masking ablation' need plain-language alternatives or definitions.
- **[380a5e3ea5e2] (severity: writing)** Simplify technical terms in Appendix sections (e.g., 'bijective function' → 'one-to-one mapping,' 'semantic truncation' → 'meaning loss,' 'heterogeneous data' → 'mixed data types').
- **[15c3ece310e2] (severity: writing)** Define common technical acronyms introduced in the revision: OCR, API, DPI (e.g., in Appendix 'Details of Experimental Setup').
- **[90e327c61d6f] (severity: science)** SAA metric formula still allows SAA=1 if Rel>=4 even when Rec<0.6. Text claims 'cited region are both correct' but formula uses OR logic (Rel>=4 OR Rec>=0.6). This logical gap remains unaddressed in Section 4.1.
- **[da19c6372ba8] (severity: writing)** Document count discrepancy persists: Section 3.1/Table 3 state 711 documents, but Appendix A (Ethics Statement) states 707 PDFs. This 4-document gap undermines data integrity claims.
- **[38ceaf428f96] (severity: science)** Circularity in ground-truth creation remains unclarified: Qwen3-VL-235B-A22B is used to identify 'Crucial Evidence' via ablation (Section 3.3), yet Qwen3-VL models are evaluated on the benchmark. No clarification provided on whether different model versions were used for annotation vs. evaluation.
- **[02308d4a7178] (severity: writing)** Tone down Claims about 'resolving' bottlenecks in Contributions; use 'mitigating' or 'addressing' to reflect LLM-based pipeline limitations.
- **[5acfbd0b568c] (severity: science)** Qualify 'Attribution Hallucination' claims in Abstract/Intro to acknowledge potential GT noise from automated pipeline (only 200/1897 human-validated).
- **[0f0357f6c79c] (severity: writing)** Clarify 'high-stakes' domain claims in Abstract/Intro to reflect that source documents are public PDFs, not sensitive records.
- **[0797277bac16] (severity: writing)** Explicitly state IRB approval or exemption status for human expert evaluation described in Appendix 'Details of Expert Evaluation'.
- **[6bc26de57319] (severity: writing)** Clarify if Personally Identifiable Information (PII) scrubbing was performed on Common Crawl documents prior to benchmark construction.
- **[e16b6109c00a] (severity: writing)** Provide a direct URL or contact method for the copyright takedown process mentioned in Appendix 'Ethical Consideration'.
- **[242296d2384b] (severity: science)** The comparison of model tiers (Table 1) is confounded by input resolution differences (Native API vs. downscaled screenshots). Re-run experiments with matched resolution or provide statistical analysis isolating this variable.
- **[44c1bd9e4108] (severity: science)** Report confidence intervals or statistical significance tests for SAA scores across models. Point estimates without variance metrics (given Temp=1.0) do not support claims of superiority.
- **[054af410b3dc] (severity: science)** Justify the sampling temperature of 1.0 for evaluation. Standard benchmarks typically use greedy decoding to minimize stochasticity in performance measurement.
- **[591006ab0b4d] (severity: science)** Compute 95% confidence intervals for all metrics in Table 2 (SAA, Recall, etc.) using bootstrap or analytical methods given N=1897. Perform pairwise significance testing (e.g., bootstrap t-test) for top model comparisons to substantiate 'best' claims.
- **[aa5450bd8869] (severity: science)** Address multiple-comparisons handling when highlighting 'best' and 'second-best' across 20 models. Explicitly state if corrections (e.g., Bonferroni, FDR) were applied to avoid false positives in ranking.
- **[c2764c2a5ed6] (severity: writing)** Fix invalid character in label. The '&' symbol in \label{Details & More Results of Experiments} is not allowed in standard LaTeX labels and breaks cross-referencing. Use underscores or colons.
- **[45d09bde6e2d] (severity: writing)** Correct typo in label. \label{appenidx: Limitations} contains a misspelling ('appenidx' vs 'appendix'), which may cause broken references.
- **[76f2560ea0de] (severity: writing)** Resolve heading hierarchy redundancy in Limitations section. A \section{Limitations...} is immediately followed by \paragraph{Limitations}. Remove the paragraph title.
- **[bc4b13deeeeb] (severity: writing)** Fix cross-reference mismatch. Text references \ref{Appendix: More Results of Experiments} but the section label is \label{Details & More Results of Experiments}. Align labels and references.
- **[c1e41bff1993] (severity: writing)** Fix typo 'Evluation' to 'Evaluation' in Appendix Prompt Templates (Prompt for Annotation Evluation).
- **[3b450b85e28b] (severity: writing)** Fix typo 'prefect' to 'perfect' in Appendix Prompt for Evaluating Answer Correctness.
- **[f2d77e1177a7] (severity: writing)** Correct grammar 'aim' to 'aims' in Appendix Limitations & Potential Negative Impacts.
- **[cf9082f81dea] (severity: writing)** Resolve data inconsistency: Section 3.1/Table 1 states 711 documents, Appendix Ethics states 707.
- **[23255a00d652] (severity: writing)** Add colon after 'Strict Attributed Accuracy (SAA)' in Section 4.1 Evaluation Metrics definition list.
- **[2eb02c632d4d] (severity: writing)** Fix double comma syntax in Appendix Details of QA Construction (Requirements list).


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 46 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
