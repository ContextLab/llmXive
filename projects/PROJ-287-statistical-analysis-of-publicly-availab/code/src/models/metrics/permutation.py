import os
import json
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer
from scipy.stats import zscore

from src.utils.logging import get_logger
from src.models.lda.fitter import fit_lda_model
from src.models.lda.aligner import TopicAligner, align_topics_across_windows
from src.data.preprocess.tokenizer import load_preprocessed_data

logger = get_logger(__name__)

def stratified_sample_by_window(
    tokenized_data: List[Dict[str, Any]],
    window_col: str = "window",
    min_samples: int = 2000
) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling to ensure representation from all windows.
    Returns min(min_samples, available) abstracts distributed proportionally.
    """
    if not tokenized_data:
        return []

    # Group by window
    windows = {}
    for record in tokenized_data:
        w = record.get(window_col, "unknown")
        if w not in windows:
            windows[w] = []
        windows[w].append(record)

    total_available = sum(len(v) for v in windows.values())
    if total_available <= min_samples:
        logger.info(f"Total available ({total_available}) <= min_samples ({min_samples}). Returning all.")
        return tokenized_data

    # Calculate proportional allocation
    sample_per_window = {}
    remaining = min_samples
    sorted_windows = sorted(windows.keys())

    # First pass: proportional allocation
    for w in sorted_windows:
        count = len(windows[w])
        # Ensure at least 1 if available, but don't exceed available
        allocation = max(1, int((count / total_available) * min_samples))
        if allocation > count:
            allocation = count
        sample_per_window[w] = allocation
        remaining -= allocation

    # Second pass: distribute remainder randomly to windows with capacity
    if remaining > 0:
        for w in sorted_windows:
            if remaining <= 0:
                break
            current = sample_per_window[w]
            capacity = len(windows[w]) - current
            if capacity > 0:
                take = min(remaining, capacity)
                sample_per_window[w] += take
                remaining -= take

    # Sample
    sampled = []
    rng = np.random.default_rng()
    for w, count in sample_per_window.items():
        if count > 0:
            indices = rng.choice(len(windows[w]), size=count, replace=False)
            sampled.extend([windows[w][i] for i in indices])

    logger.info(f"Stratified sampling complete. Sampled {len(sampled)} records from {len(windows)} windows.")
    return sampled


def run_permutation_test(
    tokenized_data: List[Dict[str, Any]],
    window_col: str = "window",
    text_col: str = "tokens",
    n_permutations: int = 1000,
    n_topics: int = 10,
    max_iter: int = 20,
    random_seed: Optional[int] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform permutation test for topic drift.
    
    Strategy:
    1. Stratified sample min(2000, available) abstracts.
    2. Compute observed JS divergence between consecutive windows using aligned topics.
    3. For each permutation:
       - Shuffle window labels of the sampled data.
       - Refit LDA models on the shuffled windows.
       - Align topics across shuffled windows.
       - Compute JS divergence.
    4. Compute p-values and effect sizes.
    
    Returns:
        Dictionary containing null distributions, p-values, and metadata.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    logger.info(f"Starting permutation test with {n_permutations} iterations.")
    logger.info(f"Loading preprocessed data...")
    
    # If data is passed directly, use it; otherwise load from file if path is implied
    # Here we assume tokenized_data is already loaded or passed in
    sampled_data = stratified_sample_by_window(tokenized_data, window_col, min_samples=2000)
    
    if len(sampled_data) < 2:
        raise ValueError("Not enough data for permutation test after stratified sampling.")

    # Identify unique windows
    unique_windows = sorted(list(set(r[window_col] for r in sampled_data)))
    if len(unique_windows) < 2:
        raise ValueError("Need at least 2 windows to compute drift.")

    logger.info(f"Working with {len(unique_windows)} windows: {unique_windows}")

    # Helper to fit LDA and get topic-word distributions for a list of records
    def fit_and_align_subset(records: List[Dict], window_label: str) -> np.ndarray:
        # Group by window internally if needed, but here we assume records are already filtered
        # Actually, we need to split by window for the refit
        window_records = {}
        for r in records:
            w = r[window_col]
            if w not in window_records:
                window_records[w] = []
            window_records[w].append(r[text_col])
        
        topic_word_matrix = {}
        vectorizer = CountVectorizer(max_df=0.95, min_df=2)
        
        for w, docs in window_records.items():
            if not docs:
                continue
            # Fit vectorizer and LDA
            try:
                X = vectorizer.fit_transform(docs)
                lda = LatentDirichletAllocation(
                    n_components=n_topics,
                    max_iter=max_iter,
                    random_state=random_seed,
                    learning_method='online' # faster for large data
                )
                lda.fit(X)
                topic_word_matrix[w] = lda.components_
            except Exception as e:
                logger.warning(f"Failed to fit LDA for window {w}: {e}")
                # Return zeros if fail to avoid crash, though ideally we should handle better
                topic_word_matrix[w] = np.zeros((n_topics, len(vectorizer.vocabulary_)))

        # Align topics across windows in this subset
        if len(topic_word_matrix) > 1:
            aligner = TopicAligner()
            aligned_matrix = aligner.align_matrices(
                topic_word_matrix, 
                window_order=list(topic_word_matrix.keys())
            )
            # Return the aligned matrix as a dict of windows -> (n_topics, vocab_size)
            # But for divergence we need proportions. 
            # Simplified for permutation: we just need the topic-word distribution to be comparable.
            # Actually, the permutation test usually shuffles labels, so we recompute the 'observed' statistic
            # on shuffled data. The 'observed' statistic was computed on real data.
            # Here we return the topic-word distributions to compute proportions or divergence directly.
            return aligned_matrix
        else:
            return topic_word_matrix

    # 1. Compute Observed Divergence (Real Data)
    logger.info("Computing observed divergence on real data...")
    # We need to compute JS divergence between consecutive windows
    # This requires topic proportions. 
    # For the permutation test, we will re-run the full pipeline (fit -> align -> prop -> div) on shuffled data.
    
    observed_divergences = []
    # To do this efficiently, we need a function that takes a list of records, fits LDA, aligns, and returns divergences
    
    def compute_window_divergences(records: List[Dict]) -> List[float]:
        # Fit LDA on each window
        window_docs = {}
        for r in records:
            w = r[window_col]
            if w not in window_docs:
                window_docs[w] = []
            window_docs[w].append(r[text_col])
        
        # Fit vectorizer on ALL data to ensure same vocab
        all_docs = [r[text_col] for r in records]
        vectorizer = CountVectorizer(max_df=0.95, min_df=2)
        try:
            X_all = vectorizer.fit_transform(all_docs)
        except ValueError:
            return [] # Not enough data

        lda_models = {}
        for w, docs in window_docs.items():
            X_w = vectorizer.transform(docs)
            if X_w.shape[0] == 0:
                continue
            lda = LatentDirichletAllocation(
                n_components=n_topics,
                max_iter=max_iter,
                random_state=random_seed,
                learning_method='online'
            )
            lda.fit(X_w)
            lda_models[w] = lda

        # Align
        if len(lda_models) < 2:
            return []
        
        aligner = TopicAligner()
        aligned_topics = aligner.align_matrices(lda_models, window_order=unique_windows)
        
        # Compute proportions for each window
        # We need to transform the documents to get topic proportions
        # But for JS divergence between windows, we usually compare the average topic distribution per window
        # Or the distribution of topic assignments.
        # Let's compute the mean topic proportion per window.
        
        window_props = {}
        for w in aligned_topics:
            lda = lda_models[w]
            # Transform the documents in this window
            X_w = vectorizer.transform(window_docs[w])
            props = lda.transform(X_w) # Shape: (n_docs, n_topics)
            mean_prop = np.mean(props, axis=0)
            # Normalize
            mean_prop = mean_prop / (np.sum(mean_prop) + 1e-10)
            window_props[w] = mean_prop

        # Compute pairwise JS divergence between consecutive windows
        from src.models.metrics.divergence import calculate_js_divergence
        divs = []
        for i in range(len(unique_windows) - 1):
            w1, w2 = unique_windows[i], unique_windows[i+1]
            if w1 in window_props and w2 in window_props:
                js = calculate_js_divergence(window_props[w1], window_props[w2])
                divs.append(js)
        return divs

    observed_divs = compute_window_divergences(sampled_data)
    logger.info(f"Observed divergences: {observed_divs}")
    observed_sum = sum(observed_divs) if observed_divs else 0.0

    # 2. Permutation Loop
    null_distributions = {f"pair_{i}": [] for i in range(len(unique_windows)-1)}
    
    logger.info(f"Running {n_permutations} permutations...")
    start_time = time.time()
    
    for i in range(n_permutations):
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation {i+1}/{n_permutations}")
        
        # Shuffle window labels
        shuffled_data = sampled_data.copy()
        # Extract window values and shuffle them
        windows = [r[window_col] for r in shuffled_data]
        np.random.shuffle(windows)
        for j, w in enumerate(windows):
            shuffled_data[j][window_col] = w
        
        # Compute divergence on shuffled data
        try:
            divs = compute_window_divergences(shuffled_data)
            if len(divs) == len(observed_divs):
                for k, d in enumerate(divs):
                    null_distributions[f"pair_{k}"].append(d)
            else:
                # Mismatch in number of windows (shouldn't happen with stratified sampling)
                pass
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {e}")
            continue

    elapsed = time.time() - start_time
    logger.info(f"Permutation test completed in {elapsed:.2f} seconds.")

    # 3. Compute P-values
    results = {
        "n_permutations": n_permutations,
        "n_topics": n_topics,
        "random_seed": random_seed,
        "observed_divergences": observed_divs,
        "p_values": [],
        "null_distributions": {}
    }

    for k in range(len(unique_windows) - 1):
        key = f"pair_{k}"
        null_dist = null_distributions[key]
        obs = observed_divs[k] if k < len(observed_divs) else 0.0
        
        if not null_dist:
            p_val = 1.0
        else:
            # P-value: proportion of null >= observed
            count_ge = sum(1 for x in null_dist if x >= obs)
            p_val = (count_ge + 1) / (len(null_dist) + 1)
        
        results["p_values"].append({
            "window_pair": f"{unique_windows[k]} -> {unique_windows[k+1]}",
            "observed": obs,
            "p_value": p_val,
            "null_mean": float(np.mean(null_dist)),
            "null_std": float(np.std(null_dist))
        })
        results["null_distributions"][key] = null_dist

    # Save results if output_dir provided
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        out_file = out_path / "permutation_results.json"
        with open(out_file, "w") as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved permutation results to {out_file}")

    return results

def main():
    """
    Entry point for running the permutation test.
    Expects processed data in data/processed/ (partitioned by window).
    """
    logger.info("Running Permutation Test (T029)...")
    
    # Load data from all windows
    # Assuming data is saved as CSVs in data/processed/ with 'window' column
    # We need to aggregate them
    data_dir = Path("data/processed")
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} not found. Please run T016 first.")
        return

    all_data = []
    for csv_file in data_dir.glob("*.csv"):
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            # Ensure tokens are lists if stored as string representation, or join if list
            # The tokenizer saves tokens as list of strings usually.
            # If saved as string "['word1', 'word2']", we need to eval or parse.
            # Let's assume the CSV has a 'tokens' column with list-like strings or actual lists.
            # For robustness, we'll convert to list if string.
            if 'tokens' in df.columns:
                df['tokens'] = df['tokens'].apply(lambda x: x if isinstance(x, list) else eval(x) if isinstance(x, str) else [])
            all_data.append(df.to_dict('records'))
        except Exception as e:
            logger.warning(f"Failed to load {csv_file}: {e}")
    
    if not all_data:
        logger.error("No data found to process.")
        return

    flat_data = [item for sublist in all_data for item in sublist]
    
    # Run test
    results = run_permutation_test(
        tokenized_data=flat_data,
        window_col="window",
        text_col="tokens",
        n_permutations=1000,
        n_topics=10,
        max_iter=20,
        random_seed=42,
        output_dir="results/stats"
    )
    
    print(json.dumps(results["p_values"], indent=2))

if __name__ == "__main__":
    main()
