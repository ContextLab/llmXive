"""
Download UCI HAR and UCI Wine datasets from verified sources.
Validates that all columns are numeric (or convertible) and saves to data/raw/.
"""
import os
import sys
import requests
import pandas as pd
from pathlib import Path
from urllib.parse import urlparse

# Add parent to path for imports if running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.config import get_seed, check_memory_limit

# Verified dataset sources (matching plan.md)
DATASETS = {
    "wine": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
        "output_file": "wine.csv",
        "has_header": False,
        "columns": [
            "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10", "C11", "C12", "C13"
        ],
        "description": "UCI Wine dataset (13 chemical constituents)"
    },
    "har": {
        "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip",
        "raw_url": "https://archive.ics.uci.edu/ml/machine-learning-databases/00240/UCI%20HAR%20Dataset.zip",
        "output_file": "har.csv",
        "has_header": True,
        "description": "UCI Human Activity Recognition dataset"
    }
}

def validate_numeric_columns(df: pd.DataFrame, dataset_name: str) -> bool:
    """
    Validate that all columns in the DataFrame are numeric.
    Returns True if valid, raises ValueError otherwise.
    """
    numeric_cols = df.select_dtypes(include=['number']).columns
    non_numeric_cols = df.columns.difference(numeric_cols)
    
    if len(non_numeric_cols) > 0:
        print(f"⚠️  Warning: Non-numeric columns found in {dataset_name}: {list(non_numeric_cols)}")
        # Try to convert numeric strings to numbers
        for col in non_numeric_cols:
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
                print(f"  Converted column '{col}' to numeric")
            except (ValueError, TypeError):
                raise ValueError(
                    f"Column '{col}' in {dataset_name} cannot be converted to numeric. "
                    f"Unique values: {df[col].unique()[:5]}..."
                )
    
    print(f"✅ {dataset_name}: All {len(df.columns)} columns validated as numeric.")
    return True

def download_wine(output_dir: Path) -> Path:
    """Download and process UCI Wine dataset."""
    url = DATASETS["wine"]["url"]
    output_path = output_dir / DATASETS["wine"]["output_file"]
    
    print(f"Downloading {DATASETS['wine']['description']}...")
    print(f"URL: {url}")
    
    # Check memory limit before proceeding
    if not check_memory_limit():
        raise MemoryError("Memory limit exceeded. Cannot proceed with download.")
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Parse the raw text
        content = response.text
        lines = content.strip().split('\n')
        
        # Create DataFrame
        data = []
        for line in lines:
            parts = [x.strip() for x in line.split(',')]
            data.append(parts)
        
        df = pd.DataFrame(data, columns=DATASETS["wine"]["columns"])
        
        # Convert to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='raise')
        
        # Validate
        validate_numeric_columns(df, "Wine")
        
        # Save
        df.to_csv(output_path, index=False)
        print(f"✅ Saved to: {output_path}")
        print(f"   Shape: {df.shape}")
        print(f"   Columns: {list(df.columns)}")
        
        return output_path
        
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download Wine dataset: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process Wine dataset: {e}")

def download_har(output_dir: Path) -> Path:
    """Download and process UCI HAR dataset."""
    url = DATASETS["har"]["raw_url"]
    output_path = output_dir / DATASETS["har"]["output_file"]
    
    print(f"Downloading {DATASETS['har']['description']}...")
    print(f"URL: {url}")
    
    # Check memory limit
    if not check_memory_limit():
        raise MemoryError("Memory limit exceeded. Cannot proceed with download.")
    
    try:
        # Download ZIP
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        # Save temporary zip
        import zipfile
        import io
        
        zip_buffer = io.BytesIO(response.content)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            # Extract to memory first
            train_features = None
            train_labels = None
            
            for name in zip_ref.namelist():
                if name.endswith('/'):
                    continue
                
                if 'train/X_train.txt' in name:
                    with zip_ref.open(name) as f:
                        content = f.read().decode('utf-8')
                        lines = content.strip().split('\n')
                        data = [list(map(float, line.split())) for line in lines]
                        train_features = pd.DataFrame(data)
                
                elif 'train/y_train.txt' in name:
                    with zip_ref.open(name) as f:
                        content = f.read().decode('utf-8')
                        lines = content.strip().split('\n')
                        labels = [int(line.strip()) for line in lines]
                        train_labels = pd.DataFrame(labels, columns=['activity'])
            
            if train_features is None or train_labels is None:
                raise RuntimeError("Could not find train features or labels in HAR dataset")
            
            # Merge
            df = pd.concat([train_features, train_labels], axis=1)
            
            # Validate
            validate_numeric_columns(df, "HAR")
            
            # Save
            df.to_csv(output_path, index=False)
            print(f"✅ Saved to: {output_path}")
            print(f"   Shape: {df.shape}")
            print(f"   Columns: {len(df.columns)} features + 1 label")
            
            return output_path
            
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download HAR dataset: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process HAR dataset: {e}")

def main():
    """Main entry point for dataset download."""
    # Set seed for reproducibility (though not strictly needed for download)
    seed = get_seed()
    print(f"🔧 Using seed: {seed}")
    
    # Determine output directory
    project_root = Path(__file__).resolve().parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    
    # Create directory if needed
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {raw_data_dir}")
    
    results = {}
    
    # Download Wine
    try:
        wine_path = download_wine(raw_data_dir)
        results["wine"] = str(wine_path)
    except Exception as e:
        print(f"❌ Wine download failed: {e}")
        results["wine"] = None
    
    # Download HAR
    try:
        har_path = download_har(raw_data_dir)
        results["har"] = str(har_path)
    except Exception as e:
        print(f"❌ HAR download failed: {e}")
        results["har"] = None
    
    # Summary
    print("\n📊 Download Summary:")
    for name, path in results.items():
        status = "✅" if path else "❌"
        print(f"  {status} {name}: {path}")
    
    # Return success only if both downloaded
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)