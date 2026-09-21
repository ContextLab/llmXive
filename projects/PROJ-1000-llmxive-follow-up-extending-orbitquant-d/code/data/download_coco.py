"""
Download and cache the MS-COCO 2017 Validation dataset.

This script fetches the 'mscoco' dataset from HuggingFace Datasets,
specifically the '2017' split, which includes both images and captions.
It uses the `datasets` library to stream/download to local cache.
Streaming is disabled to ensure the full dataset is cached locally
as required by the pipeline.

Output:
    Creates `data/raw/coco_2017_val.parquet` (or similar dataset format)
    in the project's data directory.
"""
import os
import sys
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

def main():
    config = Config()
    output_dir = config.data_raw_path
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Preparing to download MS-COCO 2017 Validation set...")
    print(f"Target directory: {output_dir}")

    try:
        from datasets import load_dataset, DatasetDict
    except ImportError:
        raise ImportError(
            "The 'datasets' library is required. Install it via: "
            "pip install datasets"
        )

    # The specific dataset configuration for MS-COCO 2017
    # 'images' contains image bytes/paths, 'annotations' contains captions
    dataset_name = "mscoco"
    dataset_config = "2017"
    dataset_split = "validation"

    print(f"Loading dataset: {dataset_name} ({dataset_config}) - {dataset_split}...")
    
    # Load with streaming=False to force local caching as per requirements
    # The dataset module 'mscoco' is standard on HF Hub
    try:
        ds = load_dataset(
            dataset_name,
            dataset_config,
            split=dataset_split,
            streaming=False,
            trust_remote_code=False
        )
    except Exception as e:
        # If the specific split name fails, try loading the whole dataset and selecting
        print(f"Initial load failed with split='{dataset_split}': {e}")
        print("Attempting to load full dataset and select validation split...")
        try:
            full_ds = load_dataset(
                dataset_name,
                dataset_config,
                streaming=False,
                trust_remote_code=False
            )
            if dataset_split in full_ds:
                ds = full_ds[dataset_split]
            else:
                available = list(full_ds.keys())
                raise ValueError(
                    f"Split '{dataset_split}' not found. Available splits: {available}"
                )
        except Exception as e2:
            raise RuntimeError(f"Failed to load MS-COCO dataset: {e2}")

    print(f"Dataset loaded successfully. Number of samples: {len(ds)}")
    print(f"Features: {ds.features}")

    # Save to parquet for efficient downstream loading
    output_file = output_dir / "coco_2017_val.parquet"
    print(f"Saving to {output_file}...")
    
    ds.save_to_disk(str(output_dir / "coco_2017_val"))
    print(f"Dataset saved to: {output_dir / 'coco_2017_val'}")

    # Also save a small metadata file for quick verification
    meta_file = output_dir / "coco_2017_val_metadata.json"
    import json
    metadata = {
        "dataset": dataset_name,
        "config": dataset_config,
        "split": dataset_split,
        "num_samples": len(ds),
        "features": str(ds.features),
        "output_path": str(output_dir / "coco_2017_val")
    }
    with open(meta_file, "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Metadata saved to: {meta_file}")
    print("Download and cache process complete.")

if __name__ == "__main__":
    main()
