import hashlib
import json
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# Import config to get paths and ensure directories exist
from config import get_paths, ensure_directories

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_dataset_from_huggingface(dataset_name: str, split: str = "train") -> Any:
    """
    Load a dataset from HuggingFace datasets library.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'openai_humaneval', 'mbpp')
        split: Dataset split to load (default: 'train')
        
    Returns:
        Dataset object from HuggingFace
    """
    try:
        from datasets import load_dataset
        dataset = load_dataset(dataset_name, split=split)
        logger.info(f"Successfully loaded {dataset_name} ({split}) split. Size: {len(dataset)}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        raise

def verify_checksums(checksum_file: Path, file_checksums: Dict[str, str]) -> bool:
    """
    Verify that calculated checksums match stored checksums.
    
    Args:
        checksum_file: Path to the stored checksums JSON file
        file_checksums: Dictionary of {filename: calculated_checksum}
        
    Returns:
        True if all checksums match, False otherwise
    """
    if not checksum_file.exists():
        logger.warning(f"Checksum file {checksum_file} does not exist. Verification skipped.")
        return False
        
    try:
        with open(checksum_file, 'r') as f:
            stored_checksums = json.load(f)
        
        all_match = True
        for filename, calculated_checksum in file_checksums.items():
            if filename not in stored_checksums:
                logger.warning(f"File {filename} not found in stored checksums.")
                all_match = False
                continue
                
            if stored_checksums[filename] != calculated_checksum:
                logger.error(f"Checksum mismatch for {filename}: "
                           f"stored={stored_checksums[filename]}, calculated={calculated_checksum}")
                all_match = False
            else:
                logger.info(f"Checksum verified for {filename}")
                
        return all_match
    except Exception as e:
        logger.error(f"Error verifying checksums: {e}")
        return False

def save_checksums(checksum_file: Path, file_checksums: Dict[str, str]) -> None:
    """Save checksums to a JSON file."""
    with open(checksum_file, 'w') as f:
        json.dump(file_checksums, f, indent=2)
    logger.info(f"Saved checksums to {checksum_file}")

def load_saved_checksums(checksum_file: Path) -> Dict[str, str]:
    """Load saved checksums from a JSON file."""
    if not checksum_file.exists():
        return {}
    try:
        with open(checksum_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading checksums: {e}")
        return {}

def download_human_eval(output_dir: Path, force_redownload: bool = False) -> Tuple[Path, Dict[str, str]]:
    """
    Download HumanEval dataset and save as JSONL with checksum verification.
    
    Args:
        output_dir: Directory to save the dataset
        force_redownload: If True, re-download even if checksums match
        
    Returns:
        Tuple of (output_file_path, checksums_dict)
    """
    ensure_directories([output_dir])
    output_file = output_dir / "humaneval.jsonl"
    checksum_file = output_dir / "humaneval_checksums.json"
    
    # Check if we can skip download
    if not force_redownload and output_file.exists():
        file_checksums = {"humaneval.jsonl": calculate_sha256(output_file)}
        if verify_checksums(checksum_file, file_checksums):
            logger.info("HumanEval dataset already downloaded and verified. Skipping.")
            return output_file, file_checksums
    
    logger.info("Downloading HumanEval dataset...")
    try:
        # Load from HuggingFace
        dataset = load_dataset_from_huggingface("openai_humaneval", split="test")
        
        # Convert to list of dicts and save as JSONL
        data_list = [dict(item) for item in dataset]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data_list:
                f.write(json.dumps(item) + '\n')
        
        logger.info(f"Saved HumanEval dataset to {output_file}")
        
        # Calculate and save checksums
        file_checksums = {"humaneval.jsonl": calculate_sha256(output_file)}
        save_checksums(checksum_file, file_checksums)
        
        return output_file, file_checksums
        
    except Exception as e:
        logger.error(f"Failed to download HumanEval: {e}")
        raise

def download_mbpp(output_dir: Path, force_redownload: bool = False) -> Tuple[Path, Dict[str, str]]:
    """
    Download MBPP dataset and save as JSONL with checksum verification.
    
    Args:
        output_dir: Directory to save the dataset
        force_redownload: If True, re-download even if checksums match
        
    Returns:
        Tuple of (output_file_path, checksums_dict)
    """
    ensure_directories([output_dir])
    output_file = output_dir / "mbpp.jsonl"
    checksum_file = output_dir / "mbpp_checksums.json"
    
    # Check if we can skip download
    if not force_redownload and output_file.exists():
        file_checksums = {"mbpp.jsonl": calculate_sha256(output_file)}
        if verify_checksums(checksum_file, file_checksums):
            logger.info("MBPP dataset already downloaded and verified. Skipping.")
            return output_file, file_checksums
    
    logger.info("Downloading MBPP dataset...")
    try:
        # Load from HuggingFace - MBPP has multiple splits, we'll use 'train'
        dataset = load_dataset_from_huggingface("mbpp", split="train")
        
        # Convert to list of dicts and save as JSONL
        data_list = [dict(item) for item in dataset]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data_list:
                f.write(json.dumps(item) + '\n')
        
        logger.info(f"Saved MBPP dataset to {output_file}")
        
        # Calculate and save checksums
        file_checksums = {"mbpp.jsonl": calculate_sha256(output_file)}
        save_checksums(checksum_file, file_checksums)
        
        return output_file, file_checksums
        
    except Exception as e:
        logger.error(f"Failed to download MBPP: {e}")
        raise

def load_model(model_name: str) -> Any:
    """
    Load a model for generation (placeholder for future implementation).
    
    Args:
        model_name: Name of the model to load
        
    Returns:
        Model object
    """
    # This is a placeholder - actual implementation will be in T011
    logger.info(f"Model loading for {model_name} not yet implemented (T011)")
    return None

def main():
    """Main function to download datasets."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download benchmark datasets')
    parser.add_argument('--human-eval', action='store_true', help='Download HumanEval dataset')
    parser.add_argument('--mbpp', action='store_true', help='Download MBPP dataset')
    parser.add_argument('--all', action='store_true', help='Download all datasets')
    parser.add_argument('--force', action='store_true', help='Force re-download even if checksums match')
    
    args = parser.parse_args()
    
    # Get paths from config
    paths = get_paths()
    data_dir = paths['data']
    human_eval_dir = data_dir / "human_eval"
    mbpp_dir = data_dir / "mbpp"
    
    if args.all or args.human_eval:
        download_human_eval(human_eval_dir, args.force)
        
    if args.all or args.mbpp:
        download_mbpp(mbpp_dir, args.force)
        
    if not args.all and not args.human_eval and not args.mbpp:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
