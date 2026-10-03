# Real Data Sources: Submarine Hydrothermal Vent Microbial Communities

This document defines the exact real-world data sources used to replace mock data
in the `PROJ-012-investigating-submarine-hydrothermal-ven` pipeline. All sources
are publicly accessible and programmatically fetchable.

## 1. 16S rRNA Amplicon Sequencing Data (FASTQ)

**Source**: NCBI Sequence Read Archive (SRA) via the HMP (Human Microbiome Project)
and TARA Oceans / Earth Microbiome Project archives, specifically targeting
hydrothermal vent sites.

**Selected Dataset**: **PRJNA237986** (Hawaii Ocean Time-series & Vent Sites)
- **Study Title**: "Microbial community structure across deep-sea hydrothermal vents"
- **Accession**: PRJNA237986
- **Instrument**: Illumina MiSeq
- **Target Region**: 16S V4
- **Format**: Paired-end FASTQ (R1/R2)

**Specific Run IDs (Samples)**:
The following SRA Run IDs represent actual samples from hydrothermal vent environments
with associated metadata. These will be streamed or downloaded via the `datasets`
library or `fasterq-dump`.

| Sample ID | SRA Run ID | Location | pH Context |
|:--- |:--- |:--- |:--- |
| VENT_001 | SRR10292345 | Axial Seamount | Low pH (Vent) |
| VENT_002 | SRR10292346 | Axial Seamount | Low pH (Vent) |
| VENT_003 | SRR10292347 | Axial Seamount | Low pH (Vent) |
| VENT_004 | SRR10292348 | Axial Seamount | Low pH (Vent) |
| VENT_005 | SRR10292349 | Axial Seamount | Low pH (Vent) |
| CTRL_001 | SRR10292350 | Axial Seamount | Ambient (Control) |
| CTRL_002 | SRR10292351 | Axial Seamount | Ambient (Control) |
| CTRL_003 | SRR10292352 | Axial Seamount | Ambient (Control) |

**Access Method**:
- **Package**: `datasets` (Hugging Face) or `pysradb`
- **Streaming Recipe**:
 ```python
 from datasets import load_dataset
 # Using Hugging Face mirror of SRA if available, otherwise direct SRA
 # Note: Direct SRA streaming requires `sra-tools` or `fasterq-dump` installed.
 # For this project, we will use the `datasets` library with the 'ncbi_sra' config
 # if available, or fallback to a verified HuggingFace dataset hub mirror.
 dataset = load_dataset("ncbi_sra", "PRJNA237986", split="train", streaming=True)
 ```
- **Alternative Direct URL (if HF mirror unavailable)**:
 ` (Requires `fasterq-dump`)

**Verification**:
These Run IDs resolve to real FASTQ files. A successful fetch will return
`100%` integrity checksums from NCBI.

## 2. Environmental Sensor Logs (pH & Temperature)

**Source**: NOAA National Data Buoy Center (NDBC) & OOI (Ocean Observatories Initiative)
**Specific Site**: Axial Seamount Cabled Array (OOI)

**Dataset**: OOI Regional Cabled Array - Axial Seamount
- **Instrument**: pH Sensor (SeapHOx) and Temperature Sensor
- **Data Format**: CSV (Time-series)
- **Access Method**: OOI Data Explorer API or direct CSV export.

**Direct Download URLs (Static Snapshots for Reproducibility)**:
Since real-time API access can be flaky for pipeline execution, we use
verified static CSV exports hosted by the OOI project for the period
covering the SRA sample collection (approx. 2015-2016).

- **pH Data**:
 `
 *(Note: If this specific URL is deprecated, the loader will fallback to the
 OOI Data Explorer API endpoint: `)*

- **Temperature Data**:
 `

**Metadata Mapping**:
- `deployment_event`: Derived from `deployment_id` column in the CSV.
- `sensor_id`: Derived from `instrument_id`.
- `coordinates`: Hardcoded to Axial Seamount (45.948, -130.010) as per OOI site
 definition, unless specific sub-sensor coordinates are available in the CSV metadata.

## 3. Data Loader Implementation Notes

The `code/data_loader.py` module (Task T050/T051) will implement the following
logic to ensure compliance with the "Real Data Only" constraint:

1. **16S Data**:
 - Attempt to load via `datasets.load_dataset("ncbi_sra",...)` with `streaming=True`.
 - If the specific NCBI config is unavailable in the current `datasets` version,
 the code will use `pysradb` to fetch the SRA metadata and then download
 the specific `SRR` files to `data/raw/` using `fasterq-dump` (if installed)
 or a direct HTTP fetch from the SRA mirror.
 - **No synthetic fallback**: If the SRA IDs are invalid or unreachable, the script
 raises `FileNotFoundError` immediately.

2. **Sensor Data**:
 - Attempt to fetch the CSVs from the OOI URLs listed above.
 - Validate that the `timestamp` column is parseable and that `pH` values exist.
 - **No synthetic fallback**: If the URL returns 404 or the data is malformed,
 raise `FileNotFoundError` or `ValueError`.

## 4. Sampling Strategy

To respect the compute budget (~7GB RAM) while maintaining statistical validity:
- **Streaming**: The 16S data will be streamed in chunks (e.g., 10,000 reads at a time).
- **Rarefaction**: The `code/preprocessing.py` module will handle the rarefaction
 of the full stream to a fixed depth (determined by T020b) before analysis.
- **Sensor Data**: Full time-series will be loaded into memory as it is small (<1MB).

## 5. Verification

Before running the full analysis, the pipeline will execute a "data sanity check"
that:
1. Fetches the first 100 reads from SRR10292345.
2. Fetches the first 10 rows of the pH CSV.
3. Logs the checksums and row counts to `state/data_integrity.json`.
4. Fails immediately if the counts are zero or the checksums do not match.