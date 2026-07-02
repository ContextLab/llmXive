---
action_items:
- id: e4a10946bbe4
  severity: science
  text: The paper claims to use a curated dataset of 62K triplets (Appendix, Sec.
    Data Curation Pipeline Details) but provides no license information, source URLs,
    or provenance for the raw video collection. Without explicit licensing (e.g.,
    CC-BY, fair use justification) and source attribution, the dataset cannot be legally
    or ethically reused, violating standard data quality requirements for reproducibility.
- id: 29b3e146cd4b
  severity: science
  text: The HGC-Bench benchmark (240 samples) is described as curated from the Internet
    with face swapping for anonymization (Appendix, Sec. HGC-Bench Details). The paper
    fails to specify the license of the source images used for the benchmark or the
    legal basis for the face-swapping operation. This creates a significant legal
    risk and prevents independent verification of the benchmark's composition.
- id: dfe6687a4726
  severity: writing
  text: The data curation pipeline relies on external APIs (Gemini-3.0/3.1, Q-Align,
    UniMatch) for filtering and captioning (Appendix, Sec. Data Curation Pipeline
    Details). The paper does not document the specific API versions, rate limits,
    or terms of service compliance for these external services. If these services
    change or become unavailable, the data pipeline becomes non-reproducible.
- id: 7f9fec2f9650
  severity: writing
  text: The paper mentions "manual verification" retaining 62K of 82K triplets (Appendix,
    Sec. Data Curation Pipeline Details) but provides no details on the verification
    protocol, inter-annotator agreement, or the specific criteria used for rejection.
    This lack of transparency in the data cleaning process undermines the reliability
    of the training data quality claims.
artifact_hash: 8ac732f80d31fee19845b13e35eb49deeae5414cb6cb993b15f1b25017de2aa1
artifact_path: projects/PROJ-598-https-arxiv-org-abs-2605-15824/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:12:48.379336Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: minor_revision
---

The paper presents a novel framework for human-garment video customization but lacks sufficient transparency regarding the data quality, provenance, and licensing of the datasets used for training and evaluation.

**Data Provenance and Licensing:**
The manuscript states in the Appendix (Section "Data Curation Pipeline Details") that a "large set of raw videos" was collected from the Internet and filtered to create a 62K training dataset. However, the paper fails to specify the source domains, the specific licenses of the collected videos, or the legal justification for their use in training a commercial-grade model. Without explicit licensing information (e.g., Creative Commons, public domain, or fair use analysis), the dataset is effectively unusable for the broader research community, and the reproducibility of the training process is compromised. Similarly, the HGC-Bench (Appendix, Section "HGC-Bench Details") is constructed from internet images with face swapping. The paper does not disclose the license of the source images or the legal framework for the face-swapping operation, which is a critical omission for a benchmark intended for public use.

**Data Curation Transparency:**
While the four-stage curation pipeline is described, the "manual verification" step (Appendix, Section "Data Curation Pipeline Details") lacks necessary detail. The paper states that 20K samples were discarded but does not provide the annotation guidelines, the number of annotators, or inter-annotator agreement metrics. This opacity makes it impossible to assess the quality and consistency of the final 62K dataset.

**External Dependencies and Link Rot:**
The data pipeline relies heavily on external APIs (Gemini-3.0/3.1, Q-Align, UniMatch) for filtering, captioning, and garment extraction (Appendix, Section "Data Curation Pipeline Details"). The paper does not document the specific API versions, endpoints, or terms of service compliance. As these services are proprietary and subject to change, the lack of version control and fallback mechanisms poses a significant risk to the long-term reproducibility of the data curation process. If these APIs are updated or discontinued, the exact dataset used for the reported results cannot be regenerated.

**Recommendation:**
The authors must provide a comprehensive data card or appendix section detailing the license, source, and collection methodology for both the training dataset and HGC-Bench. Additionally, they should document the specific versions of external tools used and provide a protocol for handling API changes to ensure future reproducibility.
