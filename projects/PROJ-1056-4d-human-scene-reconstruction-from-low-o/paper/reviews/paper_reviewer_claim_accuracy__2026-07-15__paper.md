---
action_items:
- id: 8a3e6356b259
  severity: writing
  text: Appendix Section 'GEN3C vs. Ours (Rendering Quality)' claims specific metrics
    (PSNR 20.13, SSIM 0.656, LPIPS 0.215) for the proposed method on held-out cameras.
    These exact numbers do not appear in Table 1, Table 2, or Table 6 (which lists
    'Ours w/o enh.' as 20.39/0.657/0.286). The text cites evidence that is not present
    in the provided tables, making the claim unverifiable. Update the text to match
    the table data or add a table containing these specific comparison metrics.
- id: 2ea81028368f
  severity: writing
  text: Section 3.1 states 'We also obtain human masks for each synthesized view'
    to exclude human regions during background optimization. However, the method description
    and notation {M_n^1} imply masks are only generated for the N input views using
    a segmentation model. It is unclear how masks are obtained for the 481 synthesized
    views (e.g., via propagation or re-running the model). Clarify the mask generation
    process for synthesized views to resolve this logical gap.
artifact_hash: ca7acd8eb96627c08c8e24703eed6a4159188067f14a19009f5f71e7f58b21ed
artifact_path: projects/PROJ-1056-4d-human-scene-reconstruction-from-low-o/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T02:33:29.427569Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a coherent methodology and the majority of quantitative claims are well-supported by the provided tables. The numerical values in the ablation studies (Tables 3, 4, 5) and the main results (Tables 1, 2) are internally consistent with the text descriptions.

However, there is a specific discrepancy in the Appendix under the section "GEN3C vs. Ours (Rendering Quality)". The text states: "our rendering on held-out evaluation cameras (PSNR/SSIM/LPIPS: 20.13/0.656/0.215) surpasses GEN3C's raw synthesized views (19.05/0.612/0.329)". These specific numbers (20.13, 0.656, 0.215) do not appear in any of the main tables (Table 1, Table 2) or the ablation tables (Table 6). Table 6 lists "Ours w/o enh." as 20.39/0.657/0.286, which differs from the text's claim. Since the text cites specific metrics that are not present in the data tables, the reader cannot verify this specific comparative claim. The authors should either update the text to match the numbers in Table 6 (or the correct table) or add a new table containing these specific "GEN3C vs. Ours" metrics to ensure the claim is fully supported by the evidence.

Additionally, there is a minor ambiguity in Section 3.1 regarding the generation of human masks for the 481 synthesized views. The text states, "We also obtain human masks for each synthesized view," but the mathematical notation {M_n^1} and the description of the segmentation model suggest masks are only generated for the N input views. If masks are indeed generated for all 481 synthesized views, the method description should clarify how this is achieved (e.g., by propagating masks or re-running the model), as the current text implies a contradiction between the claim and the defined variables.
