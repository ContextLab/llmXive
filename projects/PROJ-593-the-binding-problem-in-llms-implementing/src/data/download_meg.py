"""
Data ingestion module for OpenNeuro MEG dataset.
Uses Hugging Face datasets with streaming to fetch real MEG data.
"""
import os
import sys
from pathlib import Path
import pandas as pd
from datasets import load_dataset

def download_meg_streamed(output_path: str = "data/raw/meg_streamed.parquet") -> None:
    """
    Download OpenNeuro MEG dataset using streaming and save to Parquet.

    Args:
        output_path: Path to the output Parquet file.

    Raises:
        RuntimeError: If the real data fetch fails or dataset is empty.
    """
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading OpenNeuro MEG dataset with streaming...")
    try:
        # Use streaming mode to avoid downloading full dataset to memory
        # OpenNeuro ds000246 contains MEG data
        dataset = load_dataset(
            "openneuro/ds000246",
            split="train",
            streaming=True
        )

        # Convert to pandas and collect data
        # Note: We iterate through the streaming dataset to build a DataFrame
        # This is necessary because streaming datasets don't support direct to_parquet
        records = []
        batch_count = 0
        row_count = 0

        for batch in dataset:
            batch_count += 1
            # Convert batch dict to DataFrame rows
            df_batch = pd.DataFrame(batch)
            records.append(df_batch)
            row_count += len(df_batch)

            # Log progress every 10 batches
            if batch_count % 10 == 0:
                print(f"  Processed {batch_count} batches, {row_count} rows so far...")

        if not records:
            raise RuntimeError("Dataset returned no data batches.")

        # Concatenate all batches
        full_df = pd.concat(records, ignore_index=True)

        if len(full_df) == 0:
            raise RuntimeError("Final concatenated dataset is empty.")

        print(f"Saving {len(full_df)} rows to {output_path}...")
        full_df.to_parquet(output_path, index=False)

        print(f"Successfully saved MEG data to {output_path}")
        print(f"Total rows: {len(full_df)}")
        print(f"Columns: {list(full_df.columns)}")

    except Exception as e:
        # Fail loudly - no synthetic fallback
        error_msg = f"Failed to download real MEG data: {str(e)}"
        print(error_msg, file=sys.stderr)
        raise RuntimeError(error_msg) from e

if __name__ == "__main__":
    download_meg_streamed()
