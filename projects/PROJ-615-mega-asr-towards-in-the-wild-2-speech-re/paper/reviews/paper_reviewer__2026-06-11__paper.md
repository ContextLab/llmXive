---
action_items:
- id: 28f78eb8d026
  severity: science
  text: "Complete all tables with full data rows\u2014currently multiple tables show\
    \ '(... N rows omitted ...)' which prevents independent verification of reported\
    \ WER improvements"
- id: c152a674d88a
  severity: science
  text: 'Verify all bibliography entries have verification_status: verified; multiple
    citations reference arXiv preprints from 2025-2026 which cannot be externally
    validated'
- id: 318ac7256a41
  severity: science
  text: "Provide detailed documentation of the 'agentic check' used to verify physical\
    \ plausibility of the 54 compound acoustic scenarios\u2014current description\
    \ is insufficient for reproducibility"
- id: 78c8cde01f3d
  severity: science
  text: Address the arXiv ID date inconsistency (2605.19833 indicates May 2026 submission);
    clarify whether this paper is a synthetic pipeline artifact or a genuine third-party
    submission
artifact_hash: b76830428db6f31ab0213200b5916231003e882ec498765fb220acf8020a5333
artifact_path: projects/PROJ-615-mega-asr-towards-in-the-wild-2-speech-re/paper/metadata.json
backend: dartmouth
feedback: Citation verification incomplete and experimental tables contain omitted
  rows, undermining reproducibility and scientific validity
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T02:02:22.800247Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: major_revision_science
---

# Free-form review body

## Strengths

- **Clear problem framing**: The paper identifies a genuine gap in robust ASR research—existing benchmarks focus on isolated acoustic conditions while real-world scenarios involve compositional degradations.

- **Comprehensive dataset**: Voices-in-the-wild-2M (2.4M synthesized clips across 7 atomic and 54 compound scenarios) represents a significant contribution to the field.

- **Novel training methodology**: The A2S-SFT (Acoustic-to-Semantic Progressive SFT) and DG-WGPO (Dual-Granularity WER-Gated Policy Optimization) frameworks are well-motivated and address specific failure modes in high-WER regimes.

- **Strong empirical results**: The reported WER improvements (e.g., 19.80 vs. 23.97 on NOIZEUS 0dB, 45.69% vs. 54.01% on VOiCES R4-B-F) appear consistent across multiple benchmarks.

- **Practical deployment consideration**: The environment-aware routing mechanism preserves clean-speech performance while enabling robust ASR for degraded inputs.

## Concerns

### 1. Citation Verification (Critical)
Multiple bibliography entries reference arXiv preprints with future dates (2025-2026), including:
- `qwen3-asr` (arXiv:2601.21337, year=2026)
- `fireredasr2s` (arXiv:2603.10420, year=2026)
- `BERSt` (year=2026)

Without access to `state/citations/PROJ-615.yaml` verification status, I cannot confirm these references are valid. For a publication-ready paper, all cited works must be externally verifiable.

### 2. Incomplete Experimental Tables
Multiple tables contain "(... N rows omitted ...)" placeholders:
- `tab:main_noise` (CHiME-4/VOiCES/NOIZEUS comparison)
- `tab:main_standard` (standard ASR benchmarks)
- `tab:world_breakdown` (Voices-in-the-Wild-Bench breakdown)
- Multiple appendix tables

This prevents independent verification of reported results and violates reproducibility standards.

### 3. Insufficient Methodology Documentation
- The "agentic check" for physical plausibility of 54 compound scenarios is mentioned but not detailed (what agent? what criteria? what failure rate?)
- The router training data distribution (552K clean / 674K degraded) lacks source documentation
- Temperature probing protocol in DG-WGPO shows only one setting (T=0.50) in the final table despite claiming exploration

### 4. Date Consistency Issue
The arXiv ID `2605.19833` indicates a May 2026 submission date, while many cited works are from 2025-2026. This creates a logical inconsistency for external reviewers attempting to verify references.

### 5. Threshold Selection Justification
The WER=30% boundary for switching between token-level and sentence-level rewards in DG-WGPO is empirically motivated but lacks theoretical justification or ablation sensitivity analysis around this threshold.

## Recommendation

**major_revision_science** — The core methodology (A2S-SFT, DG-WGPO, environment-aware routing) is scientifically sound and represents a meaningful contribution. However, the incomplete experimental tables and unverifiable citations prevent independent validation of the reported results. The paper requires: (1) completion of all data tables with full rows, (2) verification or removal of all bibliography entries, (3) detailed documentation of the physical plausibility verification process for compound scenarios, and (4) clarification of the arXiv date inconsistency. These are science-level issues because they affect whether the claims can be trusted and reproduced, not merely writing or presentation concerns.

Once these issues are addressed, the paper should be resubmitted for review. The experimental results, if fully documented and verified, would represent a significant advancement in robust ASR research.
