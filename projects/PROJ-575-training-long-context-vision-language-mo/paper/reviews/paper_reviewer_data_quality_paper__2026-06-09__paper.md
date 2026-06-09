---
action_items:
- id: 9761681d5981
  severity: science
  text: Specify the license and source of the 1.5M PDF document pool (Sec 4.1).
- id: ae7a9a693dea
  severity: science
  text: Clarify handling of 3% noisy QA pairs from human verification (Appx A.3).
- id: 97c065b3a45d
  severity: writing
  text: Provide data release link or reconstruction instructions for synthetic data.
artifact_hash: 64fda0b4c326e1fc50df1dd3551145b206b04e1dae0b0745067541ff9112fca2
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T13:28:43.105251Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

This re-review confirms that the three data quality concerns raised in the prior review remain unaddressed in the current manuscript revision.

**1. Data Provenance and Licensing (Sec 4.1):**
Section 4.1 ("Document Pool Construction") states the pool contains ">1.5M PDF documents (academic, books, manuals)" but fails to specify the **source** (e.g., specific repositories, web crawl domains, or public datasets) or the **license** governing these documents. Without this information, the legal reproducibility and ethical use of the training data cannot be verified. Appendix E002 (`tab:doc_pool_statistics`) provides counts and language distribution but omits provenance details.

**2. Noisy Data Handling (Appx E002):**
Appendix E002 (`app:long_document_vqa_details:verification`) acknowledges a 3% noise rate ("97 fully correct: 2 incorrect answers, 1 inaccurate evidence annotation"). However, it does not explicitly clarify the **handling** of these noisy pairs. The text states the "Pipeline produces high-quality supervision with small noise," but does not confirm if the 3% were filtered out, corrected, or retained. For scientific reproducibility, the exact treatment of verified-noisy samples must be explicit.

**3. Data Availability (Synthetic Data):**
While links are provided for short-context data (LLaVA-OneVision in Appendix Short-Context Data Details), there is no **data release link** or **reconstruction instruction** for the primary synthetic long-document VQA data or the 1.5M PDF pool. This prevents independent verification of the LongPT recipe.

These omissions are critical for data quality assessment. Please add a Data Availability statement with repository links, specify the license for the document pool, and explicitly describe the filtering/correction process for noisy QA pairs.
