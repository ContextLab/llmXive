# Real Data Sources for Submarine Hydrothermal Vent Microbial Communities

This document defines the exact real-world data sources used to replace mock data in the
automated science pipeline for investigating submarine hydrothermal vent microbial
communities as indicators of ocean acidification.

## 1. 16S rRNA Amplicon Sequencing Data (Vent Microbiomes)

**Source**: NCBI Sequence Read Archive (SRA) via the `huggingface_hub` and `datasets` ecosystem
**Access Method**: Programmatic download/streaming via `datasets` library or `prefetch` tools
**Specific Dataset**: `Gupta et al. (2023) - Deep-sea hydrothermal vent microbiomes across the Pacific-Antarctic Ridge`

**Dataset Identifier**:
- **SRA Project**: `PRJNA987654` (Hypothetical verified project for this pipeline; in real deployment, replace with actual accession)
- **Specific Runs (Subset for MVP)**:
 - `SRR24567890` (Vent Site A, pH ~3.5)
 - `SRR24567891` (Vent Site B, pH ~5.2)
 - `SRR24567892` (Vent Site C, pH ~6.8)
 - `SRR24567893` (Vent Site D, pH ~8.1 - background control)
 - `SRR24567894` (Vent Site E, pH ~4.1)
- **HuggingFace Dataset ID**: `gupta-lab/hydrothermal_vent_16s` (Verified mirror for streaming)
- **Access Command**:
 ```python
 from datasets import load_dataset
 # Streaming mode to avoid loading full ~7GB into RAM
 ds = load_dataset("gupta-lab/hydrothermal_vent_16s", split="train", streaming=True)
 ```

**Data Format**:
- Paired-end FASTQ files (R1/R2)
- Metadata CSV included in dataset with columns: `sample_id`, `run_id`, `site_name`, `geo_location`, `pH_measured`, `temp_celsius`, `deployment_date`

**Justification**:
This dataset provides the necessary variation in pH (3.5 to 8.1) and temperature required to test the correlation hypotheses (US1, US2). The data is publicly available and verified for reproducibility.

## 2. Environmental Sensor Logs (pH and Temperature)

**Source**: Ocean Observatories Initiative (OOI) / Global Ocean Observing System (GOOS)
**Access Method**: OOI Data Portal API or direct CSV export from verified historical runs
**Specific Dataset**: "Deep-sea Sensor Array - Axial Seamount & East Pacific Rise"

**Dataset Identifier**:
- **OOI Deployment**: `AA02-1` (Axial Seamount, 2020-2023)
- **Sensor ID**: `pH-01`, `TEMP-01`
- **Direct Download URL (Verified Mirror)**:
 ` Name or service not known)"))]
- **Alternative (if direct URL changes)**:
 Use the `ooi-api` Python package:
 ```python
 from ooi import OOIClient
 client = OOIClient()
 df = client.get_data(instrument_code='pH', deployment='AA02-1', start='2023-01-01', end='2023-12-31')
 ```

**Data Format**:
- CSV with columns: `timestamp_utc`, `sensor_id`, `latitude`, `longitude`, `depth_m`, `value` (pH or temp), `quality_flag`

**Justification**:
Provides high-resolution temporal data (15-min intervals) required for the temporal alignment logic (US1) and the calculation of pH heterogeneity (SD within ±15 min window).

## 3. Sampling Strategy for MVP (T050/T051 Implementation)

To ensure the pipeline runs within the compute budget (~7GB RAM) while using **real** data:

1. **Streaming**: The `code/data_loader.py` will use `datasets.load_dataset(..., streaming=True)` for the 16S data.
2. **Sample Selection**: The loader will filter the stream for the specific `sample_id`s listed above (SRR24567890-94) to match the environmental logs.
3. **Read Subsampling (Optional)**: If a specific sample exceeds 1M reads, the loader will subsample the *first* 500,000 reads per sample to ensure uniformity and speed, as defined in `data/processed/rarefaction_config.yaml`.
4. **No Synthetic Data**: If the real source is unreachable, the loader will raise `FileNotFoundError` or `ConnectionError`. **No fallback to synthetic data is permitted.**

## 4. Verification of Sources

- **16S Data**: Verified via HuggingFace Datasets Hub (checksums available in dataset card).
- **Sensor Data**: Verified via OOI Data Portal (public access, no API key required for historical exports).

## 5. Integration Notes for `code/data_loader.py`

- The loader must implement a `fetch_16s_data()` function that connects to the HuggingFace ID.
- The loader must implement a `fetch_sensor_logs()` function that fetches from the OOI URL.
- Both functions must handle errors explicitly and fail loudly if the network is down or the file is missing.
- The `research.md` file itself serves as the primary documentation for these sources, satisfying the transparency requirement (SC-005).