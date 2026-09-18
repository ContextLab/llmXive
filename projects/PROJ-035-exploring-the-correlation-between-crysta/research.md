# Research Log: Constitution VII vs FR-010 Conflict

## Overview
This document records a critical conflict between **Constitution VII** (Data Provenance & Reproducibility) and **Functional Requirement FR-010** (Peer-Reviewed Literature Only) identified during the initial project setup phase.

---

## Conflict Description

### Constitution VII Requirements
- All data sources must be verifiable and reproducible
- Dataset versions must be explicitly tracked with metadata
- Source references must include DOI, PMID, or NIST ID
- Raw data checksums must be recorded in `state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml`
- **Emphasis on verifiable, programmatic access to data**

### FR-010 Requirements
- Thermal conductivity data must come **exclusively** from peer-reviewed literature or NIST Materials Data Repository
- No Materials Project thermal conductivity endpoint (unverified for this property)
- Source references must pass strict provenance validation (DOI/PMID/NIST ID regex)
- **Emphasis on source authority and peer-review status**

### The Conflict
1. **Data Availability vs. Source Authority**:
 - Constitution VII demands programmatic, reproducible data access with explicit versioning
 - FR-010 restricts sources to peer-reviewed literature/NIST, which may not always have programmatic APIs or stable versioning
 - Some high-quality peer-reviewed datasets lack machine-readable endpoints, requiring manual CSV compilation that conflicts with automated checksum tracking

2. **Versioning Granularity**:
 - Constitution VII requires exact dataset versioning (API query date, repository release tag)
 - Peer-reviewed literature is static (published once) but may have errata or updates not reflected in the original publication
 - NIST repositories may update underlying data without version tags, creating ambiguity in "exact" reproducibility

3. **Provenance Validation Rigor**:
 - Constitution VII allows any verifiable source with proper metadata
 - FR-010 imposes a stricter filter: only peer-reviewed or NIST, rejecting other potentially valid sources (e.g., preprints with DOIs, institutional repositories)
 - This creates a potential bottleneck where data exists but fails FR-010 despite satisfying Constitution VII

---

## Impact Assessment

### Pipeline Implications
- **T014b (fetch_thermal.py)**: Must implement dual validation:
 1. Check source is peer-reviewed/NIST (FR-010)
 2. Record exact metadata/versioning (Constitution VII)
- **T005b (metadata.py)**: Must capture both source type AND versioning details
- **T041 (verify_constitution_alignment.py)**: Must check for resolution before thermal fetch runs

### Risk Scenarios
1. **No Real Data Available**: If no peer-reviewed/NIST source has programmatic access, the pipeline may fail to meet minimum 50 samples (SC-001)
2. **Version Ambiguity**: If NIST updates data without version tags, reproducibility claims in Constitution VII cannot be fully satisfied
3. **Validation Conflicts**: A source with valid DOI (Constitution VII) but not in peer-reviewed list (FR-010) will be rejected, potentially reducing sample size

---

## Recommended Resolution

### Option A: Amend Constitution VII (Preferred)
- Add explicit clause: "Data sources must satisfy FR-010 (peer-reviewed/NIST) as a precondition; versioning applies to all FR-010-compliant sources"
- Clarify that "programmatic access" includes manual CSV compilation with documented scraping methodology
- Define acceptable metadata for static publications (DOI + access date + repository snapshot hash if available)

### Option B: Relax FR-010
- Allow additional sources (e.g., arXiv preprints with DOI, institutional repositories) if they satisfy Constitution VII verifiability
- Requires re-evaluation of thermal conductivity data quality standards

### Option C: Hybrid Approach
- Maintain FR-010 as primary filter
- Add "fallback" clause: If FR-010 sources yield <50 samples, temporarily permit Constitution VII-compliant sources with explicit flagging in `data/metadata.yaml`
- Document all fallback data in `research.md` with justification

---

## Action Items

1. **Immediate**: Flag for spec amendment (this document)
2. **Pre-Implementation**: T041 must verify resolution before T014b runs
3. **Documentation**: Update `specs/001-correlation-perovskites/spec.md` to reflect chosen resolution
4. **Validation**: Ensure `src/ingest/fetch_thermal.py` and `src/utils/metadata.py` implement the agreed-upon dual requirements

---

## Status
- **Conflict Identified**: [X]
- **Resolution Documented**: [X] (pending spec amendment)
- **Pipeline Blocker**: [X] (T014b cannot proceed until T041 confirms alignment)
- **Tags**: `Constitution VII`, `FR-010`, `Conflict`, `Data Provenance`, `Peer-Review`

---

## References
- Constitution VII: Data Provenance & Reproducibility
- FR-010: Peer-Reviewed Literature Only for Thermal Conductivity
- T038: Document Constitution VII vs FR-010 conflict
- T041: Verify Constitution VII alignment with FR-010
- T005b: Generate metadata.yaml with dataset versioning