# Quickstart Guide: llmXive VideoKR Follow-up

This guide provides the minimal steps to run the VideoKR reasoning cliff analysis pipeline and verify the output.

## 1. Environment Setup

Ensure you have Python 3.9 or higher installed. Create a virtual environment and install dependencies:

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Data Preparation

The pipeline requires the **VideoKR-SFT** dataset and a **Knowledge Graph**.

**Option A: Automatic Download (Recommended)**
Run the ingestion script to fetch and verify data:
```bash
python code/ingest/download_data.py
```
*Note: This script downloads data from verified sources (Hugging Face/URLs) and computes checksums.*

**Option B: Manual Placement**
If you already have the data, place the files in:
- `data/raw/videokr_sft.parquet` (or.jsonl)
- `data/raw/knowledge_graph.csv` (edges list)

## 3. Run the Pipeline

Execute the full end-to-end analysis:

```bash
python code/main.py
```

**What happens:**
1. **Ingestion**: Downloads/verifies data (if not present).
2. **Annotation**: Maps entities to graph nodes and calculates `chain_length` (hops).
3. **Analysis**: Calculates accuracy per hop, detects the "reasoning cliff" via permutation test.
4. **Sensitivity**: Sweeps thresholds to verify robustness.
5. **Reporting**: Generates plots and the final Markdown report.

## 4. Verify Outputs

After the script completes, check the `data/processed/` directory for the following key artifacts:

- **`threshold_results.json`**: Contains the optimal knot and p-value for the reasoning cliff.
- **`final_report.md`**: The complete summary of findings.
- **`accuracy_vs_hop_raw.png`**: Visual confirmation of the accuracy drop.

If `final_report.md` exists and contains a "Conclusion" section, the pipeline ran successfully.

## Troubleshooting

- **Missing Data**: If the script fails with a "Data not found" error, ensure `code/ingest/download_data.py` has been run or data is manually placed in `data/raw/`.
- **Memory Errors**: The pipeline uses chunked streaming. If you encounter memory issues, check `data/processed/memory_log.json` for peak usage.
- **Import Errors**: Ensure all dependencies in `requirements.txt` are installed.
