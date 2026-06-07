---
action_items:
- id: e5b44bb7bd61
  severity: science
  text: "Abstract and Section 5.1 claim '18.3\xD7' (4B) and '2.85\xD7' (30B) handoff\
    \ speedups, but Table e001 (tab:e1_handoff_paths) shows ~13.5\xD7 (4B cold sample)\
    \ and ~1.33\xD7 (30B cold sample) or ~1995\xD7 (4B materialization). The specific\
    \ 18.3\xD7/2.85\xD7 figures lack a clear derivation from the provided data, constituting\
    \ an unsupported quantitative claim."
- id: c02041aef35f
  severity: writing
  text: Abstract states 'Scale Out to 10^6 addressable policies' as a measured capability.
    Section e001 clarifies this is a 'sizing sketch' in the Appendix, not a measured
    result. The Abstract must qualify this claim to distinguish between measured (100k)
    and modeled (1M) evidence.
artifact_hash: b4bbb587409bb8ce9fbc13953a4d6d307cbe54e41c3196b0506aac091594e206
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T12:56:40.493701Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

**Overreach Review — Re-Review Status: Unresolved**

This re-review identifies that the critical scientific overreach flagged in the prior review remains unaddressed in the current manuscript text.

**1. Unsupported Quantitative Claims (ID: e5b44bb7bd61)**
The manuscript continues to claim specific handoff speedups ($18.3\times$ for 4B, $2.85\times$ for 30B) in Section 5.1 (e000) and the Conclusion (e002). However, Table `tab:e1_handoff_paths` (e000/e002) presents data that contradicts these figures.
*   **4B Model:** Table shows Merge Load (71.820s) vs. Adapter Load (0.036s). The calculated ratio is $\approx 1995\times$, not $18.3\times$.
*   **30B Model:** Table shows Merge Load (402.245s) vs. Adapter Load (46.455s). The calculated ratio is $\approx 8.6\times$, not $2.85\times$.
The text does not explain the derivation of $18.3\times$ and $2.85\times$. This constitutes a direct overreach where the conclusion exceeds the evidence provided in the tables. The Conclusion (e002) repeats this error, compounding the overreach.

**2. Scale Claim Qualification (ID: c02041aef35f)**
While the Abstract text is not visible in the provided chunks, the Conclusion (e002) states: "Supports $10^{6}$ addressable policies; single‑engine sweeps 100 k entries". This phrasing ("Supports") risks implying measured capability at the $10^6$ scale. The Appendix (e001) explicitly labels the $10^6$ figure as a "sizing sketch" or model, not a measured result. The main text must clearly distinguish between the *measured* 100k sweep and the *modeled* 1M capacity to avoid overclaiming system maturity.

**Recommendation:**
Correct the speedup numbers in Section 5.1 and Conclusion to match Table `tab:e1_handoff_paths`, or provide the specific experimental conditions (e.g., different baseline) that yield $18.3\times$ and $2.85\times$. Explicitly qualify the $10^6$ policy claim as "modeled capacity" in the Abstract and Conclusion.

**New Issues:**
The Conclusion (e002) has introduced a second instance of the uncorrected speedup claim, indicating the revision did not propagate the fix through the entire document.
