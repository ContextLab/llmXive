import os
import sys
import json
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from datasets import load_dataset

def run_ingestion(output_path: str = "data/processed/ingested_data.parquet"):
    """
    Ingests the Qwen-VLA/Hy-Embodied dataset.
    """
    try:
        # Load with streaming to handle large datasets
        dataset = load_dataset("Qwen-VLA/Hy-Embodied", streaming=True)
        
        # Process chunks
        all_data = []
        for batch in dataset['train']:
            # Assuming structure: text, action
            all_data.append({
                'text': batch.get('text', ''),
                'action': batch.get('action', [])
            })
        
        df = pd.DataFrame(all_data)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_parquet(output_path)
        print(f"Ingestion complete: {len(df)} samples saved to {output_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to ingest dataset: {e}")

if __name__ == "__main__":
    run_ingestion()
