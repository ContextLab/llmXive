# Systematic Literature Review (SLR) Protocol
# Project: Predicting the Impact of Composition on Vickers Hardness of Solder Alloys
# Protocol ID: PRISMA-SOLDER-001
# Date: 2023-10-27

## 1. Objectives
To systematically identify, screen, and extract data from open-access literature and databases containing solder alloy compositions and their corresponding Vickers Hardness (HV) values.

## 2. Search Strategy
The search will target the verified sources listed in `research_verified.md` and `data/config/sources.yaml`.

**Inclusion Criteria:**
- Material type: Solder alloys (Sn-based, Pb-based, Bi-based, etc.)
- Property: Vickers Hardness (HV) or convertible units (GPa, kg/mm²).
- Data completeness: Must provide elemental composition (at% or wt%) and hardness value.
- Measurement conditions: Preferably room temperature (20-25°C).

**Exclusion Criteria:**
- Alloys with >5 distinct elemental components (configurable via `MAX_ELEMENTS`).
- Hardness values without associated composition.
- Data from proprietary or inaccessible sources.

## 3. Screening Process (PRISMA Flow)
1. **Identification**: Retrieve candidate records from verified PDFs and APIs.
2. **Screening**:
 - Parse tables from PDFs using `pdfplumber`.
 - Validate elemental sums against `COMPOSITION_SUM_THRESHOLD`.
 - Filter out non-room-temperature measurements (unless flagged for manual review).
3. **Eligibility**:
 - Convert units to HV.
 - Standardize element symbols.
4. **Included**: Final dataset for ingestion.

## 4. Data Extraction
- Extracted fields: `elemental_breakdown` (dict), `hardness_hv` (float), `alloy_family` (str), `source_citation` (str), `measurement_temp_c` (float).
- Output format: CSV/JSON stored in `data/raw/`.

## 5. Handling Low N
- If total extracted N < 50, a severe warning is logged, but the pipeline proceeds with a `reduced_n_flag`.
- If N = 0, the pipeline halts with a fatal error.
