---
action_items:
- id: 4bfbfdb2390e
  severity: writing
  text: 'Table 1 (OSWorld): For Qwen3-VL-235B under MMSkills, the reported overall
    success is 39.17%. A weighted calculation using the domain counts from Appendix
    Table A1 (e.g., Chrome: 45, GIMP: 26, etc.) and the domain success rates in Table
    1 does not immediately yield 39.17%. For instance, the high performance in Chrome
    (59.91%) and GIMP (69.23%) should pull the average up significantly. The current
    overall figure seems lower than a simple weighted average of the visible domain
    scores. The authors m'
- id: 4b1b30f09d9c
  severity: writing
  text: 'Table 2 (macOSWorld): Similar concerns exist for the macOSWorld "Overall"
    column. The text claims MMSkills improve performance, but the specific aggregate
    numbers need to be mathematically consistent with the domain breakdowns provided
    in Appendix Table A1. Claim Verification in Text vs. Data:'
- id: 11ace218e3f1
  severity: writing
  text: 'Step Reduction (Section 4.3): The text claims the "largest reductions" in
    interaction steps appear for Qwen3-VL-235B. While Table 3 shows a 5.35 step reduction
    on OSWorld for this model, the same table shows a 7.67 step reduction on VAB-Minecraft
    for the same model. The text phrasing "largest reductions appearing for Qwen3-VL-235B"
    is ambiguous; it should specify "on OSWorld" or acknowledge the even larger reduction
    on VAB-Minecraft to avoid misleading the reader about the magnitude of the effec'
- id: 075cd4612acd
  severity: writing
  text: 'Behavioral Shift Metrics (Section 4.4): The claim that "exact repeated actions
    fall from 21.8% to 6.2%" for Qwen3-VL-235B is specific. However, Figure 3 (Panel
    C) does not explicitly label these percentages on the axis or in the caption.
    While the visual trend supports the claim, the specific numbers should be explicitly
    cited in the figure caption or a supplementary table to ensure the claim is fully
    supported by the visual evidence presented. Citation Accuracy: The citations for
    benchmarks (OS'
artifact_hash: d1f8365f26381f8307ae3c2777500a8f5e24701d5ef1d5e42dce305039a248a5
artifact_path: projects/PROJ-599-mmskills-towards-multimodal-skills-for-g/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:14:52.839221Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and the consistency between reported statistics, tables, and textual assertions.

**Statistical Consistency in Results Tables:**
There are potential discrepancies between the domain-level success rates and the reported "Overall" success rates in Table 1 (OSWorld) and Table 2 (macOSWorld).
1.  **Table 1 (OSWorld):** For Qwen3-VL-235B under MMSkills, the reported overall success is 39.17%. A weighted calculation using the domain counts from Appendix Table A1 (e.g., Chrome: 45, GIMP: 26, etc.) and the domain success rates in Table 1 does not immediately yield 39.17%. For instance, the high performance in Chrome (59.91%) and GIMP (69.23%) should pull the average up significantly. The current overall figure seems lower than a simple weighted average of the visible domain scores. The authors must verify if the "Overall" column is a weighted average, a simple mean, or derived from a different set of raw counts not shown in the table.
2.  **Table 2 (macOSWorld):** Similar concerns exist for the macOSWorld "Overall" column. The text claims MMSkills improve performance, but the specific aggregate numbers need to be mathematically consistent with the domain breakdowns provided in Appendix Table A1.

**Claim Verification in Text vs. Data:**
1.  **Step Reduction (Section 4.3):** The text claims the "largest reductions" in interaction steps appear for Qwen3-VL-235B. While Table 3 shows a 5.35 step reduction on OSWorld for this model, the same table shows a 7.67 step reduction on VAB-Minecraft for the same model. The text phrasing "largest reductions appearing for Qwen3-VL-235B" is ambiguous; it should specify "on OSWorld" or acknowledge the even larger reduction on VAB-Minecraft to avoid misleading the reader about the magnitude of the effect across all benchmarks.
2.  **Behavioral Shift Metrics (Section 4.4):** The claim that "exact repeated actions fall from 21.8% to 6.2%" for Qwen3-VL-235B is specific. However, Figure 3 (Panel C) does not explicitly label these percentages on the axis or in the caption. While the visual trend supports the claim, the specific numbers should be explicitly cited in the figure caption or a supplementary table to ensure the claim is fully supported by the visual evidence presented.

**Citation Accuracy:**
The citations for benchmarks (OSWorld, macOSWorld, VAB-Minecraft, LMGame-Bench) and related work (SkillWeaver, Voyager, etc.) appear to match the standard literature. However, several citations (e.g., `yang2025macosworld`, `hu2025lmgamebench`, `bai2025qwen3vl`) refer to 2025/2026 dates. Given the current date context, these are likely preprints or future-dated arXiv submissions. The reviewer cannot verify the existence of these specific versions without access to the live arXiv, but the formatting suggests they are treated as established works. If these are indeed very recent or future-dated, the authors should ensure the citation keys match the actual available versions to avoid "unreachable" or "future" citation errors in the final PDF.

**Recommendation:**
The authors should re-calculate the "Overall" success rates in Tables 1 and 2 to ensure they match the weighted averages of the domain-level data. Additionally, clarify the "largest reduction" claim in Section 4.3 to account for the VAB-Minecraft results, and explicitly label the specific percentage values in Figure 3 or its caption.
