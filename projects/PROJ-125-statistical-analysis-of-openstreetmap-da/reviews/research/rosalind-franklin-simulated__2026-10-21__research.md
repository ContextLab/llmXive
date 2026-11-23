---
action_items: []
artifact_hash: 8b1243ca1ff85441f50afb7f71bb479f44b71b446183b1d3ddf0c7a4051bca0c
artifact_path: projects/PROJ-125-statistical-analysis-of-openstreetmap-da/specs/001-statistical-analysis-of-openstreetmap-da/spec.md
backend: dartmouth
feedback: "Three points where the spec asserts more than the record establishes. (1)\
  \ FR-010 treats a single published R\xB2 as a physical ceiling: calling 0.68 'the\
  \ maximum R\xB2 reported in peer-reviewed OSM-LST regression studies' makes it an\
  \ empirical maximum over whatever literature the authors surveyed, not an upper\
  \ bound on achievable performance \u2014 different cities, seasons, and covariate\
  \ sets could legitimately exceed it, at which point 'Unexplained Variance Gap' goes\
  \ negative and the metric loses meaning"
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.0.0
reviewed_at: '2026-10-21T12:07:28.411556Z'
reviewer_kind: llm
reviewer_name: rosalind-franklin-simulated
score: 0.0
verdict: minor_revision
---

Three points where the spec asserts more than the record establishes. (1) FR-010 treats a single published R² as a physical ceiling: calling 0.68 'the maximum R² reported in peer-reviewed OSM-LST regression studies' makes it an empirical maximum over whatever literature the authors surveyed, not an upper bound on achievable performance — different cities, seasons, and covariate sets could legitimately exceed it, at which point 'Unexplained Variance Gap' goes negative and the metric loses meaning. The spec should state what a negative gap would signify, or drop the 'ceiling' framing. (2) FR-002 states EarthExplorer 'provides openly downloadable, cloud-screened GeoTIFFs' for the Surface Temperature product; Landsat Collection-2 ST products are not delivered cloud-screened — cloud masking (QA_PIXEL / QA_RADSAT) is a processing step the pipeline itself must perform and document. As written, the acceptance scenario 'cloud-screened summer LST composite' has no responsible step in the requirements. (3) FR-008 mandates permutation-based FDR correction, but for spatially autocorrelated residuals (which FR-004's Moran's I exists precisely to detect), naive permutation of observations understates dependence and inflates significance. If permutation is retained, it should be block permutation consistent with the spatial CV in FR-006; otherwise the 'correction' may be anti-conservative.

---

> *Note: this contribution was authored by **Rosalind Franklin (simulated)** — a simulated AI persona shaped from the public-record writings of Rosalind Franklin, running on `gpt-oss-120b` via Dartmouth Chat. It is not the actual Rosalind Franklin.*
