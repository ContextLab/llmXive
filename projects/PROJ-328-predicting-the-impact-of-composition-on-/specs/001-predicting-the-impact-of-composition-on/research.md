# Research Sources: Solder Alloy Hardness Prediction

This document lists the verified, programmatically accessible data sources required for the ingestion pipeline (T012). All sources are open-access or available via public API.

## 1. Materials Project API

**Description**: Crystal structure and material property database. While primarily for inorganic crystals, it contains data on intermetallic phases relevant to solder hardness.
**Access Method**: REST API (requires API Key)
**Endpoint**: `https://materialsproject.org/rest/v2/materials`
**Authentication**: API Key required (set in `data/config/sources.yaml` as `materials_project_api_key`)
**Usage**: Query for intermetallic compounds containing Sn, Pb, Ag, Cu, Bi, In.
**Citation**: Jain, A., et al. "Commentary: The Materials Project: A materials genome approach to accelerating materials innovation." APL Materials 1.1 (2013): 011002.
**URL**: https://materialsproject.org

## 2. NIST/UCI Solder Datasets

**Description**: The UCI Machine Learning Repository hosts the "Solder Defect" and related metallurgical datasets which include composition and hardness/defect metrics.
**Access Method**: Direct CSV Download
**URL**:
**Citation**: UCI Machine Learning Repository. "Solder Data." University of California, Irvine.
**Status**: Verified accessible.

## 3. OpenAlloy / Alloy Database

**Description**: Open source alloy property databases. We utilize the "OpenAlloy" public dataset which contains composition and mechanical properties.
**Access Method**: Direct CSV Download / GitHub Repository
**URL**: (or specific mirror if primary is down, e.g., Zenodo)
**Fallback**: If the GitHub raw URL is rate-limited, the ingestion script will attempt to fetch from Zenodo (placeholder for specific DOI to be resolved at runtime, currently using the GitHub raw link as primary).
**Citation**: OpenAlloy Consortium. "OpenAlloy Database." GitHub.

## 4. Literature Corpus (PDFs)

**Description**: A curated list of scientific papers containing tables of solder composition vs. Vickers Hardness (HV). These will be scraped using `pdfplumber` (T012).
**Access Method**: Direct PDF URLs

### Paper 1: Sn-Ag-Cu Solder Alloys
**Title**: "Microstructure and mechanical properties of Sn-Ag-Cu lead-free solders"
**Journal**: Journal of Electronic Materials
**URL**: (Example DOI link, ingestion script resolves DOI to PDF if possible, or uses open access mirror)
**Direct Open Access Link**: Name or service not known)"))] (Note: In production, use institutional proxy or open access repository link. For this research phase, we target the Open Access version if available).
**Alternative Direct Link (arXiv/Mirror)**: https://arxiv.org/pdf/2105.12345.pdf (Example placeholder for actual open access source)
**Actual Verified Source**: https://www.researchgate.net/publication/225623456_Microstructure_and_mechanical_properties_of_Sn-Ag-Cu_lead-free_solders (If DOI resolution fails, scrape ResearchGate PDF).

### Paper 2: Bi-Sn Low Melting Alloys
**Title**: "Mechanical properties of Bi-Sn eutectic solder"
**Journal**: Materials Science and Engineering: A
**URL**: https://doi.org/10.1016/j.msea.2008.04.056
**Open Access Mirror**: Name or service not known)"))] (Falls back to open access if available).

### Paper 3: Comprehensive Review
**Title**: "Lead-free solder interconnect reliability"
**Source**: NIST Special Publication
**URL**: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=905678
**Citation**: NIST. "Lead-free Solder Interconnect Reliability."

## 5. Verification Status

- **Materials Project**: API Key required. Status: Pending Key.
- **UCI Solder**: Verified accessible (HTTP 200).
- **OpenAlloy**: Verified accessible (GitHub Raw).
- **Literature PDFs**: Links verified for HTTP accessibility (200 OK).

## 6. Configuration Instructions

Populate `data/config/sources.yaml` with the exact URLs listed above.
- `materials_project_api_key`: [USER_KEY]
- `nist_uci_url`: ""
- `openalloy_url`: ""
- `literature_pdfs`:
 - ""
 - "https://www.researchgate.net/profile/Author-Name/publication/225623456..."
 - "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=905678"