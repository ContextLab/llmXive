---
action_items:
- id: af8adfc0f2d8
  severity: writing
  text: Abstract claims 'below 2%' accuracy on 80.4% of questions after image removal.
    Table 2 shows 1.74%/1.89% for the ablation set (n=634). Clarify if the 80.4% refers
    to the ablation subset or the full dataset, and ensure the 'below 2%' claim strictly
    matches the reported values without overgeneralizing.
- id: 530055d573ed
  severity: science
  text: Section 3.4 claims 65.7% of questions are image-essential. Summing counts
    in Table 3 for logical image-essential subtypes yields ~49.3%. Explicitly define
    which subtypes constitute the 'image-essential' category to justify the 65.7%
    figure or correct the percentage.
- id: 4ea19710b61d
  severity: writing
  text: Abstract claims MSR caps most systems below 30%. Section 4.2 says only Kimi-2.5
    and Gemini-3.1-Pro clear 30% at 32K. Table 5 shows >10 models exceed 30% at 32K.
    Revise the claim to reflect the actual distribution or specify the context length
    where the 30% cap holds.
artifact_hash: 894b3a058a7c60576126fae0e86fbf0afb5e6919dad970b01a23558253a18ccf
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:49:57.417390Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the accuracy of factual claims and their alignment with the provided evidence.

**1. Inconsistency in Image-Essential Percentages (Section 3.4 vs. Table 3)**
The paper states in Section 3.4 that "65.7% of questions are image-essential." However, Table 3 (tab:subtype_detail) provides the exact counts for each subtype. Summing the counts for subtypes that logically require image evidence (e.g., IE-Entity, IE-PrevInfo, MSR-Arithmetic, MSR-Counting, MSR-Entity) yields 389 questions. $389 / 789 \approx 49.3\%$. Even if we include all MSR and IE types, the percentage does not reach 65.7%. The text claims 65.7% are image-essential, 14.7% supportive, and 19.6% text-sufficient. The sum is 100%, but the mapping from the specific subtype counts in Table 3 to these aggregate percentages is not transparent or mathematically consistent. The authors must explicitly define which subtypes fall into the "image-essential" bucket to justify the 65.7% figure, or correct the percentage to match the data in Table 3.

**2. Overstated "Below 2%" Claim in Abstract and Section 3.4**
The abstract and Section 3.4 claim that removing evidence images drops accuracy for GPT-5.4 and Gemini-3.1-Pro to "below 2%" on the "80.4% of questions whose evidence includes images." Table 2 (tab:mm_purity) reports the ablation results for $n=634$ questions (which is $634/789 \approx 80.4\%$). The table shows GPT-5.4 at 1.74% and Gemini-3.1-Pro at 1.89%. While these are technically "below 2%," the phrasing in the abstract ("drops... below 2%") combined with the "80.4%" figure creates a slight ambiguity. The 1.74% figure is the *overall* accuracy on the ablation set. The claim is numerically supported by the table, but the text should ensure it doesn't imply that *every* question in that 80.4% subset dropped below 2%, but rather the *average* accuracy on that subset. This is a minor precision issue but worth clarifying to avoid misinterpretation of the "collapse."

**3. Inaccurate "Caps Below 30%" Claim for Multi-Session Reasoning**
The abstract states: "Multi-session reasoning caps most systems below 30%." Section 4.2 elaborates: "MSR is hardest; only Kimi-K2.5 (44.06%) and Gemini-3.1-Pro (32.17%) clear 30% at 32K." This statement is contradicted by Table 5 (tab:per_type_full_vlm). In the 32K column for the MSR type, the following models also exceed 30%:
- Qwen3.5-122B: 50.86%
- Qwen3.5-27B: 42.24%
- Qwen3.5-9B: 43.10%
- Qwen3.5-4B: 34.48%
- Qwen3.5-2B: 33.62%
- GLM-4.6V: 43.97%
- GLM-4.5V: 39.69%
- Qwen3-VL-235B (I): 54.64%
- Qwen3-VL-30B (I): 60.82%
- Qwen3-VL-8B (I): 58.25%
- Qwen3-VL-4B (I): 42.78%
- Qwen3-VL-2B (I): 50.52%

At least 12 models clear the 30% threshold at 32K. The claim that "only Kimi-K2.5 and Gemini-3.1-Pro clear 30%" is factually incorrect based on the provided table. The authors likely intended to refer to a specific subset of models (e.g., open-weight only, or a specific family) or a different context length (e.g., 128K, where performance drops significantly). As written, the claim is unsupported by the data in Table 5.

**4. Citation Consistency**
The citations appear generally consistent with the claims made (e.g., citing `kamradt2023needle` for the needle-in-a-haystack analogy). However, the claim in Section 3.4 regarding the "80.4%" figure relies on the calculation $634/789$. The text should explicitly state that the ablation was performed on the 634 image-essential/supportive questions to ensure the reader understands the denominator for the 80.4% figure.

**Conclusion**
The paper presents a strong benchmark, but the specific numerical claims in the abstract and results sections contain inconsistencies with the detailed tables. The "below 30%" cap for MSR is the most significant factual error, as it ignores a large portion of the evaluated models. The "image-essential" percentage also requires clarification to align with the subtype counts. These issues require revision to ensure the claims accurately reflect the reported data.
