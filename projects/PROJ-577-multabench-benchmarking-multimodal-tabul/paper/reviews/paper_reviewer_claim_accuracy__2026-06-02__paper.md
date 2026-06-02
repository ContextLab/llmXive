---
action_items:
- id: 2c8aeab3ffb8
  severity: writing
  text: 'Resolve dataset count discrepancy: Section 4 states ''Subsampled 20'' text-tabular
    datasets, but Appendix Table tab:text_curation_rates reports ''Accepted 23''.
    Clarify if the benchmark contains 20 or 23 text-tabular datasets.'
- id: 4a38088769e8
  severity: science
  text: 'Verify DINO-v3 citation: Cite simeoni_dinov3_2025 for DINO-v3-small. DINOv2
    is the public standard; confirm DINOv3 exists and the citation accurately reflects
    the model used.'
- id: fac48c5c759c
  severity: writing
  text: 'Refine GBDT comparison citation: The claim ''surpassing GBDTs'' cites GBDT
    invention papers (e.g., breiman_random_2001). Cite the benchmark paper (erickson_tabarena_2025)
    for the performance comparison claim.'
artifact_hash: 6787a87df841d43fd2785f288cbdae2d1c09b5ec14bf84bfd0cf81559d785c80
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T11:12:14.738279Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

**Claim Accuracy Review**

The paper makes several specific factual claims regarding benchmark composition, model performance, and literature comparisons. While internal consistency is generally high, there are notable discrepancies and citation precision issues that affect claim accuracy.

**1. Benchmark Composition Discrepancy**
In Section 4 (MulTaBench), the text states regarding text-tabular curation: "Subsampled 20." This aligns with the Abstract claim of "40 datasets (20 image-tabular, 20 text-tabular)." However, Appendix Table `tab:text_curation_rates` explicitly reports "Accepted 23" datasets for the Text-Tabular pool.
*   **Issue:** This creates a factual conflict: is the benchmark size 40 (20+20) or 43 (20+23)?
*   **Impact:** The claim "MulTaBench: 40 datasets" may be inaccurate if 23 text datasets were retained.
*   **Location:** Section 4, Paragraph 2 vs. Appendix, Table `tab:text_curation_rates`.

**2. Citation Accuracy for Model Comparisons**
The Introduction claims: "Tabular Foundation Models... surpassing GBDTs \cite{breiman_random_2001, chen_xgboost_2016, ke_lightgbm_2017, prokhorenkova_catboost_2018}."
*   **Issue:** The cited sources are the original papers defining Random Forest, XGBoost, LightGBM, and CatBoost. They do not contain the comparison data showing TFMs surpassing them. The performance comparison is evidenced by `erickson_tabarena_2025` (TabArena), which is cited earlier in the sentence for "SOTA".
*   **Recommendation:** Move the GBDT citation keys to the definition of the models, and cite `erickson_tabarena_2025` for the "surpassing" claim to ensure the source supports the specific factual assertion.
*   **Location:** Introduction, Paragraph 1.

**3. Model Existence Verification**
The paper cites `simeoni_dinov3_2025` for "DINO-v3-small" embeddings (Section 3, Appendix).
*   **Issue:** DINOv2 is the current public standard. "DINO-v3" is not a widely recognized public model as of the paper's context. If this model is hallucinated or internal-only without public release, the experimental claims relying on it (Section 5 Robustness) are unsupported by verifiable evidence.
*   **Recommendation:** Confirm the existence of `DINO-v3` and the `simeoni_dinov3_2025` citation. If unavailable, switch to DINOv2 and update citations.
*   **Location:** Section 3, "The Curation Pipeline"; Appendix `app:curation_tar_training`.

**4. Scope of Theoretical Citations**
The claim "Embeddings act as lossy summaries \cite{weller_theoretical_2025}" appears in the Introduction.
*   **Issue:** `weller_theoretical_2025` is cited elsewhere (Related Work) for "RAG systems fail on simple cases." If this paper focuses on Retrieval-Augmented Generation rather than general tabular embeddings, the application of the "lossy summary" claim to the broader tabular context may be an over-extension of the source's findings.
*   **Location:** Introduction, Paragraph 2.

**Conclusion**
The core experimental results (TAR > Frozen) are internally consistent with the provided figures and tables. However, the benchmark size inconsistency and the potential hallucination of the DINO-v3 model require correction to ensure factual accuracy before acceptance.
