import random
import hashlib
import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger
from code.config import SEED, N_PER_LANGUAGE

log = get_logger(__name__)

def get_sha256(file_path):
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def stream_and_sample():
    """
    Stream codeparrot/github-code and perform deterministic reservoir sampling.
    Note: codeparrot/github-code is primarily Python. The logic handles multiple 
    languages if present in the dataset.
    """
    log.info(f"Starting streaming download of codeparrot/github-code with N={N_PER_LANGUAGE} per language.")
    
    # Use the exact source specified in the task
    try:
        ds = load_dataset("codeparrot/github-code", split="train", streaming=True)
    except Exception as e:
        log.error(f"Failed to fetch dataset: {e}")
        raise

    random.seed(SEED)
    
    # Reservoirs for target languages
    target_langs = ["python", "java"]
    reservoirs = {lang: [] for lang in target_langs}
    counts = {lang: 0 for lang in target_langs}
    
    # To prevent infinite loops or timeouts on massive streams in a test environment,
    # we process a large but finite window. In a full production run, we'd process all.
    # 100k rows is typically enough to fill a 1k reservoir for common languages.
    MAX_ROWS_TO_SCAN = 100_000 
    
    for i, item in enumerate(ds):
        if i >= MAX_ROWS_TO_SCAN:
            log.info(f"Reached scan limit of {MAX_ROWS_TO_SCAN} rows.")
            break
        
        # The dataset codeparrot/github-code is Python-centric. 
        # We check for a language field or default to 'python'.
        lang = item.get("language", "python").lower()
        if lang not in reservoirs:
            continue
        
        counts[lang] += 1
        # Reservoir Sampling (Algorithm R)
        if len(reservoirs[lang]) < N_PER_LANGUAGE:
            reservoirs[lang].append(item)
        else:
            j = random.randint(0, counts[lang] - 1)
            if j < N_PER_LANGUAGE:
                reservoirs[lang][j] = item

    # Flatten reservoirs into a single list
    all_samples = []
    for lang, samples in reservoirs.items():
        log.info(f"Sampled {len(samples)} rows for language: {lang}")
        for s in samples:
            all_samples.append({
                "repo_name": s.get("repo_name", "unknown"),
                "language": lang,
                "content": s.get("content", ""),
                "status": "raw"
            })

    if not all_samples:
        raise RuntimeError("No data was sampled from the dataset.")

    # Create DataFrame and add unique IDs
    df = pd.DataFrame(all_samples)
    df.insert(0, "id", range(len(df)))
    
    # Write to Parquet
    output_path = paths.data("processed", "raw_chunks.parquet")
    df.to_parquet(output_path, index=False)
    log.info(f"Saved raw chunks to {output_path}. Total rows: {len(df)}")
    
    # Record SHA-256 checksum
    checksum = get_sha256(output_path)
    checksum_path = paths.data("checksums.txt")
    with open(checksum_path, "w") as f:
        f.write(f"{output_path.name}: {checksum}\n")
    log.info(f"Checksum recorded in {checksum_path}")

if __name__ == "__main__":
    stream_and_sample()
