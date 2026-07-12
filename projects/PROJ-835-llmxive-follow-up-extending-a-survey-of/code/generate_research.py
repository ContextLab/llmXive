"""
T008: Generate research.md artifact with dataset verification details.

This script verifies the availability and properties of the target dataset
(audio_bench/jailbreak_v1) and generates a comprehensive research.md file
documenting the dataset verification details.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import from project config
from config import set_seed, ensure_directories
from utils.memory_monitor import get_current_memory_mb

# Set seed for reproducibility
set_seed(42)

# Ensure directories exist
ensure_directories()

# Constants
DATASET_NAME = "audio_bench/jailbreak_v1"
FALLBACK_DATASET = "audio_bench"
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
RESEARCH_DOC_PATH = DATA_DIR / "research.md"

def verify_dataset_availability(dataset_name: str) -> Dict[str, Any]:
    """
    Verify if a dataset is available via the datasets library.
    
    Args:
        dataset_name: Name of the dataset to verify
        
    Returns:
        Dictionary with verification results
    """
    result = {
        "name": dataset_name,
        "available": False,
        "error": None,
        "features": None,
        "num_splits": 0,
        "sample_size": None
    }
    
    try:
        from datasets import load_dataset, get_dataset_config_names
        
        # Check if dataset exists
        try:
            configs = get_dataset_config_names(dataset_name)
            result["configs"] = configs
        except Exception as e:
            result["configs_error"] = str(e)
            # Try without configs
            pass
        
        # Try to load a small sample
        try:
            dataset = load_dataset(dataset_name, split="train", streaming=True)
            sample = next(iter(dataset))
            result["available"] = True
            result["features"] = list(sample.keys())
            result["sample_size"] = len(str(sample))
            result["preview"] = {k: str(v)[:100] for k, v in sample.items()}
        except Exception as e:
            result["error"] = str(e)
            result["available"] = False
            
    except ImportError:
        result["error"] = "datasets library not installed"
        result["available"] = False
    except Exception as e:
        result["error"] = str(e)
        result["available"] = False
        
    return result

def generate_research_doc(verification_results: Dict[str, Any]) -> str:
    """
    Generate the research.md document content.
    
    Args:
        verification_results: Dictionary containing dataset verification results
        
    Returns:
        Markdown content for research.md
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_memory = get_current_memory_mb()
    
    doc = f"""# Research: Dataset Verification Report

**Generated**: {timestamp}  
**Project**: PROJ-835-llmxive-follow-up-extending-a-survey-of  
**Task**: T008 - Generate research.md artifact with dataset verification details  

---

## 1. Executive Summary

This document verifies the availability and properties of the target dataset for the
LlmXive follow-up study on latent-space jailbreak detection. The primary dataset
target is **audio_bench/jailbreak_v1**, with **audio_bench** as a fallback.

### Current System State
- **Memory Usage**: {current_memory:.2f} MB
- **Dataset Primary**: {DATASET_NAME}
- **Dataset Fallback**: {FALLBACK_DATASET}

---

## 2. Dataset Verification Results

### 2.1 Primary Dataset: {DATASET_NAME}

"""
    
    primary = verification_results.get(DATASET_NAME, {})
    if primary.get("available"):
        doc += f"""**Status**: ✅ **Available**  
**Features**: {', '.join(primary.get("features", []))}  
**Configs**: {', '.join(primary.get("configs", [])) if "configs" in primary else "N/A"}  
**Sample Preview**:  
```json
{json.dumps(primary.get("preview", {}), indent=2)}
```
"""
    else:
        doc += f"""**Status**: ❌ **Not Available**  
**Error**: {primary.get("error", "Unknown error")}  
**Configs Error**: {primary.get("configs_error", "N/A")}  
"""
    
    doc += """
### 2.2 Fallback Dataset: audio_bench

"""
    
    fallback = verification_results.get(FALLBACK_DATASET, {})
    if fallback.get("available"):
        doc += f"""**Status**: ✅ **Available**  
**Features**: {', '.join(fallback.get("features", []))}  
**Configs**: {', '.join(fallback.get("configs", [])) if "configs" in fallback else "N/A"}  
**Sample Preview**:  
```json
{json.dumps(fallback.get("preview", {}), indent=2)}
```
"""
    else:
        doc += f"""**Status**: ❌ **Not Available**  
**Error**: {fallback.get("error", "Unknown error")}  
"""
    
    doc += """
---

## 3. Data Schema Expectations

Based on the project's data-model.md and contracts, the dataset is expected to contain:

- **Audio Files**: Raw audio data (WAV, MP3, or similar formats)
- **Labels**: Binary classification labels (jailbreak vs. benign)
- **Metadata**: Optional fields such as speaker ID, duration, source, etc.

### Expected Fields (from contracts/dataset.schema.yaml)
- `audio`: Audio data path or bytes
- `label`: Binary label (0 = benign, 1 = jailbreak)
- `id`: Unique identifier for the sample
- `metadata`: Optional dictionary with additional information

---

## 4. Download Strategy

The data download pipeline (T009) will implement the following strategy:

1. **Primary Attempt**: Load `audio_bench/jailbreak_v1` via the `datasets` library
2. **Fallback**: If primary fails, attempt to load `audio_bench`
3. **Verification**: Validate downloaded data against `contracts/dataset.schema.yaml` (T014b)
4. **Storage**: Save raw data to `data/raw/` with checksum verification

---

## 5. Constraints & Requirements

### Memory Constraints
- **Peak RAM Limit**: ≤ 6.5 GB (enforced by memory_monitor.py)
- **Batch Processing**: Data will be processed in batches to stay within memory limits

### Runtime Constraints
- **Maximum Runtime**: ≤ 6 hours for full pipeline
- **Streaming**: Use streaming mode for large datasets to avoid loading entire dataset into memory

### Data Integrity
- **Checksum Verification**: All downloaded files will be verified against expected checksums
- **Schema Validation**: Data will be validated against defined schemas before processing

---

## 6. Next Steps

1. **T009**: Implement data download script with fallback logic
2. **T014b**: Implement schema validation for downloaded data
3. **T010**: Implement audio preprocessing pipeline
4. **T011**: Implement embedding extraction pipeline

---

## 7. References

- **Project Plan**: `specs/001-llmxive-follow-up-extending-a-survey-of/plan.md`
- **Data Model**: `specs/001-llmxive-follow-up-extending-a-survey-of/data-model.md`
- **Contracts**: `contracts/dataset.schema.yaml`, `contracts/embedding.schema.yaml`
- **Constitution Principles**: See `results/methodology_notes.md` for statistical methodology overrides

---

*This document was automatically generated by T008 implementation script.*
"""
    
    return doc

def main():
    """Main entry point for T008."""
    print("Starting T008: Generate research.md artifact...")
    
    # Verify both datasets
    print(f"Verifying primary dataset: {DATASET_NAME}")
    primary_result = verify_dataset_availability(DATASET_NAME)
    
    print(f"Verifying fallback dataset: {FALLBACK_DATASET}")
    fallback_result = verify_dataset_availability(FALLBACK_DATASET)
    
    verification_results = {
        DATASET_NAME: primary_result,
        FALLBACK_DATASET: fallback_result
    }
    
    # Generate research document
    print("Generating research.md document...")
    research_content = generate_research_doc(verification_results)
    
    # Ensure data directory exists
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write research.md
    print(f"Writing research.md to {RESEARCH_DOC_PATH}...")
    with open(RESEARCH_DOC_PATH, "w", encoding="utf-8") as f:
        f.write(research_content)
    
    print(f"✅ T008 completed successfully. Research document written to {RESEARCH_DOC_PATH}")
    
    # Print summary
    print("\n--- Verification Summary ---")
    for name, result in verification_results.items():
        status = "✅ Available" if result.get("available") else "❌ Not Available"
        print(f"{name}: {status}")
        if result.get("error"):
            print(f"  Error: {result['error']}")

if __name__ == "__main__":
    main()