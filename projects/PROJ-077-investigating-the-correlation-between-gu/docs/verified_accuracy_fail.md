# Verified Accuracy Fail Status

## Current Status: FAIL

The pipeline currently fails the "Verified Accuracy" check because **no verified public URLs** exist for the UK Biobank microbiome and cognitive performance data required for this analysis.

## Reason

The UK Biobank data is not publicly available via direct download URLs. Access requires:
1. Application approval through the UK Biobank access management system
2. Institutional approval and data usage agreements
3. Download of data through the approved UK Biobank Research Analysis Platform or secure data transfer mechanisms

## Pipeline Configuration

Due to the lack of public URLs, the pipeline is configured to run **ONLY on local data** placed in the `data/raw/` directory.

### Required Local Data Files

The following files must be present in `data/raw/` for the pipeline to execute:

1. **Microbiome Data**: `microbiome_otu_table.csv` or `microbiome_asv_table.csv`
 - Columns: `participant_id`, OTU/ASV count columns (integer counts)

2. **Cognitive Performance Data**: `cognitive_data.csv`
 - Columns: `participant_id`, `fluid_intelligence`, `age`, `sex`, `bmi`

3. **Dietary Data** (for DQS calculation): `dietary_data.csv`
 - Columns: `participant_id`, `Total Fruits`, `Whole Fruits`, `Total Vegetables`, `Greens and Beans`, `Whole Grains`, `Dairy`, `Total Protein Foods`, `Seafood and Plant Proteins`, `Refined Grains`, `Sodium`, `Empty Calories`

## Resolution Path

To resolve this FAIL status, one of the following must occur:

1. **Obtain UK Biobank Access**:
 - Apply for access at https://www.ukbiobank.ac.uk/
 - Download the required datasets
 - Place files in `data/raw/` following the naming conventions above

2. **Alternative Verified Source**:
 - If a verified public dataset becomes available (e.g., through a different repository with equivalent data), update `docs/data_source_resolution.md` with the new URL and recipe
 - Update `code/data_fetcher.py` to fetch from the new verified source

3. **Local Data Provision**:
 - Continue using local data in `data/raw/` for development and testing
 - Document the exact data source and acquisition method used for reproducibility

## Impact on Execution

- The pipeline will **fail loudly** with a `FileNotFoundError` if required local files are missing
- No synthetic or mock data will be generated as fallback (per Constitution constraints)
- The `ALLOW_LOCAL_DATA` configuration flag (default: True) permits local execution but does not suppress the initial data availability check

## Related Tasks

- T049: Document verified data source status
- T050: Implement data fetcher with local fallback
- T055: Document exact data access recipe
- T056: Update spec.md to allow local data sources

## Last Updated

2024-01-15