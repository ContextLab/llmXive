---
action_items:
- id: d5405d2e7553
  severity: fatal
  text: The paper claims to release 4,695 unique images under CC-BY-4.0 (Ethics Statement,
    App 2.1), but the sourcing method (iCrawler from public web) implies third-party
    copyright. The license statement 'Third-party images not relicensed' contradicts
    the claim of releasing them under CC-BY-4.0. A clear, verifiable license manifest
    for every image URL is required to resolve this legal ambiguity.
- id: c3b8f2078dce
  severity: science
  text: The dataset construction relies on 'public web searches' via iCrawler (App
    2.1) but lacks a formal datasheet detailing the specific search queries, timestamps,
    and source URLs for the 4,695 images. Without a persistent, versioned registry
    of source URLs and their original licenses, the dataset is subject to link rot
    and cannot be audited for provenance or copyright compliance.
- id: bdddcaea6aea
  severity: writing
  text: The paper states that 'no two questions share the same source image' (App
    2.1) and uses perceptual hashing for deduplication. However, it does not provide
    the hash values or the specific deduplication threshold logic in a machine-readable
    format. This prevents independent verification of the uniqueness claim and the
    integrity of the dataset against future link rot or image replacement.
- id: b9070e996d0e
  severity: writing
  text: The 'Ethics Statement' mentions a '7-day removal' takedown contact but does
    not provide the specific contact mechanism (email, form) or the current status
    of any takedown requests. This lack of transparency regarding the data removal
    process undermines the ethical compliance of the dataset release.
artifact_hash: 894b3a058a7c60576126fae0e86fbf0afb5e6919dad970b01a23558253a18ccf
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:04:26.249524Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_data_quality_paper
score: 0.0
verdict: full_revision
---

The data quality review of "MemLens" identifies critical gaps in provenance, licensing, and version control that threaten the reproducibility and legal validity of the benchmark.

**Licensing and Provenance Contradiction:**
The paper asserts in the Ethics Statement and Appendix 2.1 that 4,695 images are "released under CC-BY-4.0." However, the same section admits the images originate from "public web searches" and that "Third-party images *not* relicensed." This is a direct contradiction. You cannot release third-party copyrighted material under a CC-BY-4.0 license without explicit permission from the original rights holders. The current statement suggests the authors are distributing potentially infringing content or misrepresenting the license of the assets. A complete, itemized license manifest for every image in the dataset is required to resolve this.

**Link Rot and Source Verification:**
The dataset relies on "public web searches" via `iCrawler` (Appendix 2.1). The paper does not provide a persistent, versioned registry of the source URLs, search queries, or timestamps for the 4,695 images. Without this metadata, the dataset is highly susceptible to link rot. If the original web pages are removed or altered, the benchmark becomes un-reproducible and un-auditable. The authors must release a `manifest.json` or similar artifact containing the source URL, original license, and a snapshot hash (or archived link) for every image to ensure long-term integrity.

**Deduplication and Uniqueness Verification:**
While the paper claims a "persistent URL registry enforces global image uniqueness" and uses perceptual hashing (pHash) with a Hamming distance threshold of 6 (Appendix 2.1), it fails to provide the actual hash values or the specific logic used for the threshold. This prevents independent verification of the "no duplicate images" claim. To ensure data quality, the authors should release the pHash values for all images in the dataset.

**Takedown Mechanism Transparency:**
The Ethics Statement mentions a "7-day removal" takedown contact but does not specify the contact method (e.g., email address, web form) or the current status of any takedown requests. This lack of transparency regarding the data removal process is a significant oversight for a dataset involving web-scraped content.

In summary, the benchmark's data quality is currently compromised by ambiguous licensing, lack of source provenance, and insufficient version control. These issues must be addressed before the dataset can be considered reliable or legally sound.
