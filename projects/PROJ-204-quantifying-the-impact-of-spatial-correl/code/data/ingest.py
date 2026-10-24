"""
code/data/ingest.py
-------------------
Implements the ingestion pipeline: download -> align -> mask -> unify.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd
from llmxive_toolkit import paths, get_logger
from data.download import download_from_verified_source
from data.align import create_aligned_dataset
from preprocess.calibrate import calibrate_and_log

log = get_logger(__name__)

def _write_ingestion_log(messages: List[str]) -> None:
    log_path = paths.results("ingestion_log.txt")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        for line in messages:
            f.write(line + "\n")

def _write_ingestion_stats(n_requested: int, n_processed: int, exclusions: List[Dict]) -> None:
    stats = {
        "ingestion_success_rate": n_processed / n_requested if n_requested else 0.0,
        "total_requested": n_requested,
        "total_processed": n_processed,
        "exclusions": exclusions,
    }
    stats_path = paths.results("ingestion_stats.json")
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

def ingest_and_filter_dataset(config_path: str = None) -> pd.DataFrame:
    raw_dir = paths.data("raw")
    processed_dir = paths.data("processed")
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Download
    feasibility = {} 
    try:
        samples = download_from_verified_source(feasibility)
    except Exception as e:
        log.error(f"Data download failed: {e}")
        raise

    n_requested = len(samples)
    
    # 2. Align & Mask
    records = []
    exclusions = []
    
    for sample in samples:
        try:
            sample_id = sample["sample_id"]
            element_files = [
                sample["pb_map_filename"],
                sample["i_map_filename"],
                sample["ma_map_filename"],
            ]
            
            # Alignment to 512x512 grid (implicitly handled by create_aligned_dataset 
            # if reference is 512x512, but we ensure it here)
            aligned_maps = create_aligned_dataset(
                raw_dir=raw_dir,
                element_files=element_files,
                reference_key="Pb",
            )
            
            # Force 512x512 for the project spec
            from data.align import resample_map
            target_shape = (512, 512)
            final_maps = {}
            for elem, arr in aligned_maps.items():
                if arr.shape != target_shape:
                    final_maps[elem] = resample_map(arr, target_shape)
                else:
                    final_maps[elem] = arr

            # Masking
            masked_paths = {}
            mask_percentages = []
            for elem, arr in final_maps.items():
                masked_arr, stats = calibrate_and_log(image=arr)
                out_path = processed_dir / f"{sample_id}_{elem}_masked.npy"
                np.save(out_path, masked_arr)
                masked_paths[elem] = str(out_path)
                mask_percentages.append(stats["total_mask_fraction"])

            record = {
                "sample_id": sample_id,
                "Pb_map_path": masked_paths.get("Pb"),
                "I_map_path": masked_paths.get("I"),
                "MA_map_path": masked_paths.get("MA"),
                "pce": float(sample["pce"]),
                "j_sc": float(sample["j_sc"]),
                "v_oc": float(sample["v_oc"]),
                "mask_percentage": float(np.mean(mask_percentages)),
                "eds_status": "complete",
                "co_location_status": "unknown",
                "depth_validation_status": "unknown",
            }
            records.append(record)
            
        except Exception as e:
            log.warning(f"Sample {sample['sample_id']} failed: {e}")
            exclusions.append({"sample_id": sample.get("sample_id", "unknown"), "reason": str(e)})

    df = pd.DataFrame(records)
    unified_path = processed_dir / "unified_dataset.csv"
    df.to_csv(unified_path, index=False)
    
    _write_ingestion_log([f"{ex['sample_id']}: {ex['reason']}" for ex in exclusions])
    _write_ingestion_stats(n_requested, len(df), exclusions)
    
    return df

def main() -> None:
    ingest_and_filter_dataset()

if __name__ == "__main__":
    main()
