# Quickstart Guide

## Prerequisites
1. Install dependencies:
 ```bash
 pip install -r requirements.txt
 ```
2. Set CDS API Key:
 ```bash
 export CDS_API_KEY="your_api_key_here"
 ```

## Execution Pipeline
Run the following commands in order to execute the full research pipeline:

1. **Download Moral Machine Data**:
 ```bash
 python code/download_moral_machine.py
 ```

2. **Validate Sources**:
 ```bash
 python code/validate_sources.py
 ```

3. **Define Bounding Box**:
 ```bash
 python code/define_bbox.py
 ```

4. **Fetch ERA5 Full Dataset (T002c)**:
 ```bash
 python code/fetch_era_full.py
 ```
 *Note: This step may take a long time depending on the bounding box size and network speed.*

5. **Stream & Save ERA5 Chunks (T002d)**:
 ```bash
 python code/stream_era5.py
 ```

6. **Ingest & Merge**:
 ```bash
 python code/ingestion.py
 ```

7. **Modeling**:
 ```bash
 python code/modeling.py
 ```

8. **Robustness Analysis**:
 ```bash
 python code/robustness.py
 ```