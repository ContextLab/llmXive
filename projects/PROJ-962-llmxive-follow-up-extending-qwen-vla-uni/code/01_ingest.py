import os
import sys
import json
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from datasets import load_dataset

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.seeds import set_global_seed
from utils.data_loader import load_qwen_vla_dataset, DataFetchError
from utils.kinematics import extract_kinematic_features, normalize_joint_angles
from utils.config import get_data_params

def run_ingestion():
    """
    Ingests the Qwen-VLA dataset, extracts kinematic features, and saves processed data.
    """
    set_global_seed(42)
    print("Starting Ingestion Pipeline...")

    # Load configuration
    data_params = get_data_params()
    dataset_name = data_params.get("dataset_name", "Qwen-VLA/Hy-Embodied")
    streaming = data_params.get("streaming", True)

    try:
        # Load dataset
        print(f"Loading dataset: {dataset_name}")
        dataset = load_qwen_vla_dataset(dataset_name, streaming=streaming)
        
        # Process data (simplified for this task)
        # In a real scenario, this would iterate, extract features, and normalize
        processed_data = []
        
        # Mock processing for demonstration if dataset is empty or small
        # Real implementation would loop over dataset
        if len(dataset) == 0:
            raise ValueError("Dataset is empty. Cannot proceed with ingestion.")

        # Extract features (mocked for structure)
        # Assuming dataset has 'text' and 'action' columns
        for item in dataset:
            features = extract_kinematic_features(item['action'])
            normalized = normalize_joint_angles(features)
            processed_data.append({
                "text": item['text'],
                "action": item['action'],
                "features": normalized
            })

        # Save to parquet
        df = pd.DataFrame(processed_data)
        output_path = os.path.join(PROJECT_ROOT, "data", "processed", "raw_trajectories.parquet")
        df.to_parquet(output_path)
        print(f"Ingestion complete. Saved to {output_path}")
        
    except DataFetchError as e:
        print(f"CRITICAL: Data fetch failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during ingestion: {e}")
        raise

if __name__ == "__main__":
    run_ingestion()
