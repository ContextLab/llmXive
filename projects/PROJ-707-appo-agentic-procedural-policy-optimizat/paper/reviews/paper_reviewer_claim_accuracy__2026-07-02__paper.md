---
action_items:
- id: 467aff23f0cc
  severity: science
  text: Theorem 1 (Variance Reduction) claims a strict inequality Var(g_APPO) <= Var(g_base)
    - Delta, but the proof in Appendix A.1 only establishes non-strict inequality
    (<=) and relies on an assumption that sigma_i are not all equal without explicitly
    stating this condition in the theorem statement. The theorem should clarify the
    condition for strict reduction or remove the Delta term if equality is possible.
- id: c0f78c4c01b4
  severity: writing
  text: Table 1 reports APPO outperforming ARPO by '+7.9%' on Llama3.1-8B, but the
    raw numbers (57.4 vs 55.3) represent an absolute difference of 2.1 points, not
    a 7.9% relative improvement. The percentage calculation appears inconsistent with
    the reported absolute scores, potentially misleading readers about the magnitude
    of gains.
- id: c09eca0795df
  severity: writing
  text: The paper claims APPO was evaluated on '13 benchmarks' in the abstract and
    conclusion, but Table 1 lists 10 datasets and Table 2 lists 4 datasets (with WebWalker
    appearing in both). The total count of unique benchmarks is ambiguous, and the
    claim of '13' is not explicitly reconciled with the presented tables.
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T09:34:24.085056Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their support by the provided evidence.

**Theorem Validity and Proof Consistency**
Theorem 1 (Variance Reduction) in Section 3.3 asserts that the APPO gradient estimator satisfies $\mathrm{Var}(g_{\mathrm{APPO}})\le \mathrm{Var}(g_{\mathrm{base}})-\Delta_\Omega({\rm BS})$ with $\Delta_\Omega({\rm BS})\ge 0$. However, the proof in Appendix A.1 derives $\sum \frac{\sigma_i^2}{n_i^{\mathrm{APPO}}} \le \sum \frac{\sigma_i^2}{n_i^{\mathrm{uniform}}}$, which implies $\mathrm{Var}(g_{\mathrm{APPO}}) \le \mathrm{Var}(g_{\mathrm{base}})$. The strict reduction term $\Delta_\Omega$ is only non-zero if the variances $\sigma_i$ are not all equal. The theorem statement does not explicitly condition the strict inequality on the heterogeneity of decision point variances, creating a gap between the claim and the proof. If all decision points have identical reward variance, the claimed reduction $\Delta$ would be zero, making the strict inequality form potentially misleading.

**Quantitative Reporting Accuracy**
In Table 1, the authors report a performance gain for APPO over ARPO on the Llama3.1-8B backbone as "+7.9%". The table shows APPO at 57.4 and ARPO at 55.3. The absolute difference is 2.1 points. A relative improvement calculation yields $(57.4 - 55.3) / 55.3 \approx 3.8\%$, not 7.9%. The 7.9% figure appears to be a calculation error or a mislabeling of the absolute difference (perhaps confusing it with the gain over a different baseline or a different metric). This discrepancy significantly misrepresents the magnitude of the improvement claimed in the abstract and conclusion.

**Benchmark Count Consistency**
The abstract and conclusion state that experiments were conducted on "13 benchmarks." Table 1 lists 10 datasets (AIME24, AIME25, MATH500, GSM8K, MATH, WebWalker, HotpotQA, 2Wiki, Musique, Bamboogle). Table 2 lists 4 datasets (General AI Assistant, WebWalkerQA, Humanity's Last Exam, Xbench). Note that "WebWalker" (Table 1) and "WebWalkerQA" (Table 2) likely refer to the same benchmark, and "General AI Assistant" corresponds to GAIA. Even assuming distinct datasets, the count is ambiguous. If WebWalker/WebWalkerQA are the same, the total is 12. If they are distinct, it is 13. The paper does not explicitly clarify this overlap or list the 13 distinct names in a single consolidated list, making the "13 benchmarks" claim difficult to verify directly from the tables.

**Citation Support**
The citations generally appear to support the claims regarding prior work (e.g., ARPO, GRPO). However, the specific claim that "token entropy alone does not reliably reflect their impact" (Abstract) is supported by Figure 1(b), which is described in the text but the figure image is not visible. Based on the text description, the claim is internally consistent with the provided analysis, but the quantitative support relies on the unseen figure. The claim regarding the "13 benchmarks" is the most significant factual discrepancy requiring correction.
