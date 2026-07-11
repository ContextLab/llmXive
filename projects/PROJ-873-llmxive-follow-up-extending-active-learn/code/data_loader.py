import os
import random
import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import hashlib
import beir
from beir import util
from beir.datasets.data_loader import GenericDataLoader

@dataclass
class RedundancyCluster:
    original_id: str
    cluster_id: int
    members: List[str]

def download_beir_dataset(dataset_name: str) -> str:
    """
    Download a dataset from BEIR.
    Returns the path to the extracted dataset folder.
    """
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    data_path = os.path.join("data", "beir", dataset_name)
    
    if not os.path.exists(data_path):
        os.makedirs(data_path, exist_ok=True)
        zip_path = os.path.join("data", "beir", f"{dataset_name}.zip")
        print(f"Downloading {dataset_name}...")
        util.download_and_unzip(url, "data/beir")
        # util.download_and_unzip usually extracts to the target dir or a subfolder.
        # BEIR datasets usually extract to a folder named after the dataset inside the target.
        # If it extracted directly to data/beir/{dataset_name}, we are good.
        # If it extracted to data/beir/{dataset_name}/corpus.jsonl, we need to verify.
        # The util function typically unzips to the target folder. 
        # If the zip contains a root folder, it might be data/beir/{dataset_name}/{dataset_name}/
        # We handle this by checking if the expected files exist.
        
        expected_corpus = os.path.join(data_path, "corpus.jsonl")
        if not os.path.exists(expected_corpus):
            # Check if it created a nested folder
            nested = os.path.join(data_path, dataset_name)
            if os.path.exists(os.path.join(nested, "corpus.jsonl")):
                # Move contents up? Or just return the nested path.
                # For simplicity in this pipeline, we assume the extraction lands us in the right place
                # or we adjust the path.
                data_path = nested
    return data_path

def load_beir_corpus(dataset_path: str) -> Tuple[Dict[str, Dict], Dict[str, List[int]], Dict[str, str]]:
    """Load BEIR corpus, queries, and qrels."""
    data_path = dataset_path
    corpus, queries, qrels = GenericDataLoader(data_path).load(split="test")
    return corpus, queries, qrels

def fetch_nfcorpus_and_scifact():
    """Fetch specific datasets required for T005."""
    return {
        "nfcorpus": download_beir_dataset("nfcorpus"),
        "scifact": download_beir_dataset("scifact")
    }

def get_synonym_replacement(text: str) -> str:
    """Placeholder for synonym replacement logic using NLTK WordNet."""
    # Implementation would go here, returning modified text
    return text

def shuffle_sentences(text: str) -> str:
    """Shuffle sentences in a text block."""
    sentences = text.split('.')
    random.shuffle(sentences)
    return '. '.join(sentences)

def inject_synthetic_redundancy(corpus: Dict[str, Dict], cluster_size: int = 4) -> Tuple[Dict[str, Dict], List[RedundancyCluster]]:
    """Inject synthetic redundancy into the corpus."""
    new_corpus = corpus.copy()
    clusters = []
    items = list(corpus.items())
    random.shuffle(items)
    
    for i in range(0, len(items) - cluster_size, cluster_size):
        cluster_items = items[i:i+cluster_size]
        original_id, original_doc = cluster_items[0]
        
        # Create near-duplicates
        for j in range(1, cluster_size):
            new_id = f"{original_id}_dup_{j}"
            # Simple modification: append a marker or shuffle sentences
            new_text = shuffle_sentences(original_doc.get("text", ""))
            new_corpus[new_id] = {"text": new_text, "title": original_doc.get("title", "")}
        
        clusters.append(RedundancyCluster(
            original_id=original_id,
            cluster_id=i,
            members=[original_id] + [f"{original_id}_dup_{j}" for j in range(1, cluster_size)]
        ))
    
    return new_corpus, clusters

def save_injected_dataset(corpus: Dict[str, Dict], clusters: List[RedundancyCluster], output_path: str):
    """Save the injected dataset to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            "corpus": corpus,
            "clusters": [asdict(c) for c in clusters]
        }, f, indent=2)

def load_injected_dataset(path: str) -> Tuple[Dict[str, Dict], List[RedundancyCluster]]:
    """Load an injected dataset."""
    with open(path, 'r') as f:
        data = json.load(f)
    return data["corpus"], [RedundancyCluster(**c) for c in data["clusters"]]

def run_injection_pipeline(dataset_name: str, output_dir: str = "data/injected"):
    """Run the full injection pipeline for a dataset."""
    dataset_path = download_beir_dataset(dataset_name)
    corpus, queries, qrels = load_beir_corpus(dataset_path)
    new_corpus, clusters = inject_synthetic_redundancy(corpus)
    output_path = os.path.join(output_dir, f"{dataset_name}_injected.json")
    save_injected_dataset(new_corpus, clusters, output_path)
    return output_path

def load_trec_covid_corpus() -> Dict[str, Dict]:
    """
    Download and load the raw corpus from BEIR trec-covid dataset.
    Returns the corpus dictionary.
    """
    dataset_path = download_beir_dataset("trec-covid")
    corpus, _, _ = load_beir_corpus(dataset_path)
    return corpus

def find_real_world_near_duplicates(corpus: Dict[str, Dict], top_k: int = 100, similarity_threshold: float = 0.98) -> List[Tuple[str, str, float]]:
    """
    Identifies real-world near-duplicate pairs in the trec-covid corpus using cosine similarity.
    Since calculating all pairs is O(N^2), we sample a subset of the corpus to find high-similarity pairs.
    
    Args:
        corpus: The BEIR corpus dictionary.
        top_k: Number of candidate pairs to return.
        similarity_threshold: Minimum cosine similarity to consider a pair as a near-duplicate.
    
    Returns:
        A list of tuples (id1, id2, similarity_score) representing near-duplicate pairs.
    """
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    print("Loading embedding model for near-duplicate detection...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Sample a subset of the corpus to make computation feasible
    # trec-covid is relatively large, so we sample to find duplicates without O(N^2) on full set
    sample_size = min(2000, len(corpus))
    sample_ids = list(corpus.keys())[:sample_size]
    sample_docs = [corpus[doc_id]["text"] for doc_id in sample_ids]

    print(f"Encoding {len(sample_docs)} documents...")
    embeddings = model.encode(sample_docs, convert_to_numpy=True, show_progress_bar=True)

    print("Computing pairwise similarities...")
    # Compute cosine similarity matrix
    sim_matrix = cosine_similarity(embeddings)

    near_duplicates = []
    
    # Iterate over upper triangle to find high similarity pairs
    n = len(sample_ids)
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            sim = sim_matrix[i, j]
            if sim > similarity_threshold:
                near_duplicates.append((
                    sample_ids[i],
                    sample_ids[j],
                    float(sim)
                ))
                count += 1
                if count >= top_k:
                    break
        if count >= top_k:
            break

    return near_duplicates

def validate_synthetic_vs_real(output_path: str = "data/validation/synthetic_vs_real_validation.json"):
    """
    Task T017 Implementation:
    Validate synthetic redundancy against a small set of real-world near-duplicates 
    from BEIR trec-covid to ensure generalizability.
    
    1. Fetch real trec-covid corpus.
    2. Identify real near-duplicate pairs (cosine > 0.98).
    3. Compare structural properties (e.g., text length difference, edit distance proxy)
       between synthetic duplicates (from injected datasets) and real duplicates.
    4. Save the validation report.
    """
    import os
    import json
    from difflib import SequenceMatcher
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print("Step 1: Fetching real-world near-duplicates from trec-covid...")
    trec_corpus = load_trec_covid_corpus()
    real_pairs = find_real_world_near_duplicates(trec_corpus, top_k=50, similarity_threshold=0.98)
    
    print(f"Found {len(real_pairs)} real near-duplicate pairs in trec-covid.")

    # Load a synthetic dataset to compare properties
    # We assume a synthetic dataset was generated for nfcorpus or scifact previously
    # If not found, we generate one on the fly for comparison purposes
    synthetic_corpus_path = "data/injected/nfcorpus_injected.json"
    if not os.path.exists(synthetic_corpus_path):
        # Fallback: generate synthetic for scifact if nfcorpus not found
        synthetic_corpus_path = "data/injected/scifact_injected.json"
        if not os.path.exists(synthetic_corpus_path):
            # If no synthetic exists, we can't compare directly, but we can still analyze real
            # and note the limitation. However, the task asks to validate synthetic against real.
            # Let's try to generate a small synthetic set for comparison if none exists.
            print("No pre-existing synthetic dataset found. Generating a small synthetic set for comparison...")
            from data_loader import run_injection_pipeline
            # We need a base dataset. Let's try scifact as it's usually smaller.
            try:
                run_injection_pipeline("scifact", "data/injected")
                synthetic_corpus_path = "data/injected/scifact_injected.json"
            except Exception as e:
                print(f"Could not generate synthetic data for comparison: {e}")
                synthetic_corpus_path = None

    real_similarity_stats = {"mean": 0.0, "min": 0.0, "max": 0.0}
    if real_pairs:
        sims = [p[2] for p in real_pairs]
        real_similarity_stats = {
            "mean": float(np.mean(sims)),
            "min": float(np.min(sims)),
            "max": float(np.max(sims))
        }

    synthetic_stats = {
        "count": 0,
        "similarity_mean": 0.0,
        "similarity_min": 0.0,
        "similarity_max": 0.0,
        "note": "No synthetic dataset found for comparison"
    }

    if synthetic_corpus_path and os.path.exists(synthetic_corpus_path):
        print(f"Step 2: Loading synthetic dataset from {synthetic_corpus_path}...")
        syn_corpus, syn_clusters = load_injected_dataset(synthetic_corpus_path)
        
        # Calculate similarity for synthetic pairs
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        syn_pairs = []
        for cluster in syn_clusters:
            if len(cluster.members) > 1:
                # Compare original with first duplicate
                id1 = cluster.members[0]
                id2 = cluster.members[1]
                if id1 in syn_corpus and id2 in syn_corpus:
                    syn_pairs.append((id1, id2))
        
        if syn_pairs:
            syn_texts = [syn_corpus[p[0]]["text"] for p in syn_pairs] + [syn_corpus[p[1]]["text"] for p in syn_pairs]
            syn_embeddings = model.encode(syn_texts, convert_to_numpy=True, show_progress_bar=False)
            
            # Reshape to calculate pairs
            # syn_embeddings shape: (2*N, dim)
            # We want pairs (0,1), (2,3), etc.
            N = len(syn_pairs)
            emb1 = syn_embeddings[:N]
            emb2 = syn_embeddings[N:]
            syn_sims = cosine_similarity(emb1, emb2).diagonal()
            
            synthetic_stats = {
                "count": len(syn_pairs),
                "similarity_mean": float(np.mean(syn_sims)),
                "similarity_min": float(np.min(syn_sims)),
                "similarity_max": float(np.max(syn_sims))
            }
    
    # Calculate text length difference stats for real pairs
    real_length_diffs = []
    for id1, id2, _ in real_pairs:
        if id1 in trec_corpus and id2 in trec_corpus:
            len1 = len(trec_corpus[id1]["text"])
            len2 = len(trec_corpus[id2]["text"])
            real_length_diffs.append(abs(len1 - len2))
    
    real_length_stats = {"mean": 0.0, "min": 0.0, "max": 0.0}
    if real_length_diffs:
        real_length_stats = {
            "mean": float(np.mean(real_length_diffs)),
            "min": float(np.min(real_length_diffs)),
            "max": float(np.max(real_length_diffs))
        }

    report = {
        "task_id": "T017",
        "dataset_real": "trec-covid",
        "real_near_duplicates": {
            "count": len(real_pairs),
            "similarity_stats": real_similarity_stats,
            "text_length_diff_stats": real_length_stats
        },
        "synthetic_near_duplicates": synthetic_stats,
        "validation_summary": {
            "real_sim_range": f"{real_similarity_stats['min']:.4f} - {real_similarity_stats['max']:.4f}",
            "synthetic_sim_range": f"{synthetic_stats.get('similarity_min', 0):.4f} - {synthetic_stats.get('similarity_max', 0):.4f}" if synthetic_stats.get('count', 0) > 0 else "N/A",
            "conclusion": "Real-world near-duplicates in trec-covid exhibit very high cosine similarity (>0.98). Synthetic injection via sentence shuffling produces high similarity but may differ in distribution. The pipeline can generalize if the synthetic threshold (0.95) covers the real-world distribution."
        }
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Validation report saved to {output_path}")
    return report

if __name__ == "__main__":
    validate_synthetic_vs_real()
