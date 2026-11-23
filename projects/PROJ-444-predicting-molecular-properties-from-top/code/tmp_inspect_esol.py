"""
Utility script to download the ESOL CSV (if not present) and print its column names.
This aids verification that the ingestion script correctly maps the source columns
to the required schema (smiles, logP).
"""
import pathlib, json, sys
import pandas as pd
import requests

RAW_PATH = pathlib.Path("data/raw/esol.csv")
if not RAW_PATH.is_file():
    url = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv"
    print(f"Downloading ESOL dataset from {url} ...")
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_PATH.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print("Download complete.")
df = pd.read_csv(RAW_PATH, nrows=5)
print("First 5 rows column names:", list(df.columns))
# Output a small JSON with column list for downstream use
out = {"columns": list(df.columns)}
pathlib.Path("data/processed/esol_columns.json").write_text(json.dumps(out))
print("Wrote column list to data/processed/esol_columns.json")
sys.exit(0)