---
action_items:
- id: 3dbb93289dc4
  severity: writing
  text: In Section 4.1, the claim of a 1.6% GenEval improvement over DiffusionOPD
    (0.833) is inconsistent with the table data (0.849 vs 0.833 yields ~1.92%). Correct
    the percentage or verify the baseline used.
- id: 86777ecf3810
  severity: writing
  text: In Section 4.1, clarify the specific alpha/beta pairs defining 'train-only'
    and 'eval-only' CFG baselines to ensure the 7.6% and 1.4% improvement claims are
    unambiguously supported by Table 3.
- id: 2e7e67a65fcc
  severity: writing
  text: In Section 4.1, the 8.5% GEditBench improvement over the Edit source (4.930
    vs 5.347) is accurate (8.46%), but ensure all percentage claims in the text are
    rounded consistently to avoid minor discrepancies.
artifact_hash: 345c406695aa2dde1374386d01dde68941ce2b695d941d4807a3dc21f8ee698f
artifact_path: projects/PROJ-797-danceopd-on-policy-generative-field-dist/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T15:40:29.390181Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with the provided data in the tables and text.

The manuscript makes several specific quantitative claims in Section 4.1 (Main Results) regarding performance improvements. A detailed cross-check of these claims against Table 2 (Main Results) and Table 3 (CFG Absorption Diagnostics) reveals minor discrepancies in the reported percentage improvements, which, while small, affect the precision of the factual claims.

1.  **GenEval Improvements (Section 4.1):** The text states DanceOPD improves GenEval over the T2I source by 2.0% and over the strongest composition baseline (DiffusionOPD) by 1.6%.
    *   **T2I Source:** Table 2 lists T2I at 0.832 and DanceOPD at 0.849. The relative improvement is $(0.849 - 0.832) / 0.832 \approx 2.04\%$. The claim of 2.0% is accurate to one decimal place.
    *   **DiffusionOPD Baseline:** Table 2 lists DiffusionOPD at 0.833. The relative improvement is $(0.849 - 0.833) / 0.833 \approx 1.92\%$. The text claims 1.6%. This is a notable discrepancy (approx. 0.3 percentage points difference). It is possible the authors compared against a different baseline or used a different rounding convention, but as written, the claim "1.6%" is not supported by the numbers in Table 2.

2.  **GEditBench Improvements (Section 4.1):** The text claims an 8.5% improvement over the edit source.
    *   **Edit Source:** Table 2 lists the Edit source at 4.930 and DanceOPD at 5.347. The relative improvement is $(5.347 - 4.930) / 4.930 \approx 8.46\%$. The claim of 8.5% is accurate.
    *   **Best Reproduced OPD Baseline:** The text claims an 8.1% improvement over the best reproduced OPD baseline. In Table 2, DiffusionOPD (4.947) is the highest OPD baseline. $(5.347 - 4.947) / 4.947 \approx 8.09\%$. This matches the 8.1% claim.

3.  **CFG Absorption (Section 4.1):** The text claims a 7.6% improvement over train-only absorption and 1.4% over eval-only CFG.
    *   **Train-only:** Table 3 shows Train-only (3.5, 1.0) at 5.422. $(5.833 - 5.422) / 5.422 \approx 7.58\%$. Matches 7.6%.
    *   **Eval-only:** Table 3 shows Eval-only (1.0, 7.0) at 5.751. $(5.833 - 5.751) / 5.751 \approx 1.42\%$. Matches 1.4%.
    *   These claims are accurate, but the text would benefit from explicitly stating the $\alpha$ and $\beta$ values used for "train-only" and "eval-only" to prevent ambiguity, as the table contains multiple rows.

4.  **Ablation Claims (Section 4.2):** The text states hard routing improves over soft mixing by 15.2% (MSE) and 10.6% (KL).
    *   **MSE:** Table 4 shows Hard Routing (Step alternation, MSE) at 5.751 and Soft-teacher mixing (Soft-teacher MSE) at 4.994. $(5.751 - 4.994) / 4.994 \approx 15.16\%$. Matches 15.2%.
    *   **KL:** Table 4 shows Hard Routing (KL) at 5.501 and Soft-teacher mixing (Soft-teacher KL) at 4.976. $(5.501 - 4.976) / 4.976 \approx 10.55\%$. Matches 10.6%.
    *   These claims are accurate.

The primary issue is the 1.6% vs 1.92% discrepancy in the GenEval comparison against DiffusionOPD. This suggests a potential calculation error in the manuscript text or a misidentification of the baseline. Given the precision required in scientific claims, this should be corrected to ensure the text accurately reflects the data in Table 2. Additionally, clarifying the specific parameter settings for "train-only" and "eval-only" in the CFG section would strengthen the factual clarity of those claims.
