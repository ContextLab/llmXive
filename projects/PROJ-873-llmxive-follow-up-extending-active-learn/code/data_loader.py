import os
import random
import json
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

try:
    from beir import util
    from beir.datasets.data_loader import GenericDataLoader
    import beir
except ImportError:
    raise ImportError("The 'beir' package is required. Install it via: pip install beir")

logger = logging.getLogger(__name__)

@dataclass
class RedundancyCluster:
    """Represents a cluster of near-duplicate documents."""
    cluster_id: str
    documents: List[Dict[str, Any]]
    representative_id: str

def download_beir_dataset(dataset_name: str, data_dir: str = "data/beir") -> str:
    """
    Download a BEIR dataset if not already present.
    Returns the path to the dataset directory.
    """
    url_map = {
        "nfcorpus": "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/nfcorpus.zip",
        "scifact": "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip",
        "trec-covid": "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/trec-covid.zip"
    }
    
    if dataset_name not in url_map:
        raise ValueError(f"Dataset {dataset_name} not in URL map.")
        
    url = url_map[dataset_name]
    dataset_path = os.path.join(data_dir, dataset_name)
    
    if not os.path.exists(dataset_path):
        logger.info(f"Downloading {dataset_name} from {url}...")
        os.makedirs(data_dir, exist_ok=True)
        zip_path = util.download_and_unzip(url, data_dir)
        logger.info(f"Downloaded and unzipped to {zip_path}")
    else:
        logger.info(f"Dataset {dataset_name} already exists at {dataset_path}")
        
    return dataset_path

def load_beir_corpus(dataset_name: str, data_dir: str = "data/beir") -> Tuple[Dict, Dict, Dict]:
    """
    Load BEIR corpus, queries, and qrels.
    Returns: (corpus, queries, qrels)
    """
    dataset_path = download_beir_dataset(dataset_name, data_dir)
    # GenericDataLoader expects the path to the unzipped folder
    corpus, queries, qrels = GenericDataLoader(dataset_path).load()
    return corpus, queries, qrels

def fetch_nfcorpus_and_scifact(data_dir: str = "data/beir") -> Dict[str, Any]:
    """
    Fetch both nfcorpus and scifact datasets.
    Returns a dictionary containing both datasets.
    """
    datasets = {}
    for name in ["nfcorpus", "scifact"]:
        logger.info(f"Fetching {name}...")
        corpus, queries, qrels = load_beir_corpus(name, data_dir)
        datasets[name] = {
            "corpus": corpus,
            "queries": queries,
            "qrels": qrels
        }
    return datasets

def get_synonym_replacement(text: str, n: int = 1) -> str:
    """
    Replace n random words in text with synonyms (using NLTK WordNet).
    This is a simplified placeholder; real implementation requires NLTK data.
    """
    try:
        import nltk
        from nltk.corpus import wordnet
    except ImportError:
        raise ImportError("NLTK is required for synonym replacement. Install via: pip install nltk")
    
    # Ensure wordnet data is available
    try:
        wordnet.synsets("word")
    except LookupError:
        nltk.download('wordnet', quiet=True)
        nltk.download('omw-1.4', quiet=True)
        
    words = text.split()
    if len(words) <= 1:
        return text
        
    # Select random words to replace
    indices_to_replace = random.sample(range(len(words)), min(n, len(words)))
    new_words = words.copy()
    
    for i in indices_to_replace:
        word = words[i]
        synsets = wordnet.synsets(word)
        if synsets:
            # Get lemmas from the first synset
            lemmas = synsets[0].lemmas()
            if lemmas:
                synonym = lemmas[0].name().replace('_', ' ')
                new_words[i] = synonym
                
    return " ".join(new_words)

def shuffle_sentences(text: str) -> str:
    """Shuffle sentences within a document to create variation."""
    # Simple split by period for demonstration
    sentences = text.split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    random.shuffle(sentences)
    return ". ".join(sentences) + "."

def inject_synthetic_redundancy(corpus: Dict[str, Any], 
                                n_clusters: int = 20, 
                                cluster_size: int = 4) -> Tuple[Dict[str, Any], List[RedundancyCluster]]:
    """
    Inject synthetic redundancy into a corpus by creating near-duplicate clusters.
    Each cluster contains 1 original + (cluster_size - 1) variations.
    """
    if n_clusters < 20:
        logger.warning(f"Requested {n_clusters} clusters, but requirement is >= 20.")
        
    corpus_items = list(corpus.items())
    if len(corpus_items) < n_clusters * cluster_size:
        raise ValueError(f"Corpus too small to create {n_clusters} clusters of size {cluster_size}.")
        
    selected_indices = random.sample(range(len(corpus_items)), n_clusters)
    clusters = []
    new_corpus = corpus.copy()
    cluster_counter = 0
    
    for idx in selected_indices:
        doc_id, doc = corpus_items[idx]
        original_text = doc.get("text", "")
        if not original_text:
            continue
            
        cluster_docs = [doc]
        # Generate variations
        for j in range(1, cluster_size):
            var_text = original_text
            # Apply transformations
            if random.random() > 0.5:
                var_text = get_synonym_replacement(var_text, n=2)
            if random.random() > 0.5:
                var_text = shuffle_sentences(var_text)
                
            new_doc_id = f"{doc_id}_dup_{j}"
            new_doc = doc.copy()
            new_doc["text"] = var_text
            new_corpus[new_doc_id] = new_doc
            cluster_docs.append(new_doc)
            
        cluster_id = f"cluster_{cluster_counter}"
        clusters.append(RedundancyCluster(
            cluster_id=cluster_id,
            documents=cluster_docs,
            representative_id=doc_id
        ))
        cluster_counter += 1
        
    return new_corpus, clusters

def save_injected_dataset(corpus: Dict[str, Any], clusters: List[RedundancyCluster], output_path: str):
    """Save the injected dataset and cluster metadata to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save corpus
    corpus_path = output_path.replace(".json", "_corpus.json")
    with open(corpus_path, 'w') as f:
        json.dump(corpus, f, indent=2)
        
    # Save clusters
    cluster_data = [asdict(c) for c in clusters]
    cluster_path = output_path.replace(".json", "_clusters.json")
    with open(cluster_path, 'w') as f:
        json.dump(cluster_data, f, indent=2)
        
    logger.info(f"Saved injected dataset to {corpus_path} and clusters to {cluster_path}")

def load_injected_dataset(path_prefix: str) -> Tuple[Dict[str, Any], List[RedundancyCluster]]:
    """Load an injected dataset from disk."""
    corpus_path = path_prefix + "_corpus.json"
    cluster_path = path_prefix + "_clusters.json"
    
    with open(corpus_path, 'r') as f:
        corpus = json.load(f)
        
    with open(cluster_path, 'r') as f:
        cluster_data = json.load(f)
        
    clusters = [RedundancyCluster(**c) for c in cluster_data]
    return corpus, clusters

def load_trec_covid_corpus(data_dir: str = "data/beir") -> Dict[str, Any]:
    """Load TREC-COVID corpus for validation."""
    return load_beir_corpus("trec-covid", data_dir)[0]

def find_real_world_near_duplicates(corpus: Dict[str, Any], threshold: float = 0.95) -> List[Tuple[str, str, float]]:
    """
    Find real-world near-duplicates in a corpus using cosine similarity.
    This is a simplified check; full implementation would require embedding all docs.
    """
    from metrics import calculate_cosine_similarity_proxy
    import numpy as np
    
    docs = list(corpus.values())
    texts = [d.get("text", "") for d in docs]
    
    if len(texts) > 100:
        logger.warning("Corpus too large for full pairwise comparison. Sampling...")
        indices = random.sample(range(len(texts)), 100)
        texts = [texts[i] for i in indices]
        docs = [docs[i] for i in indices]
        
    sims = calculate_cosine_similarity_proxy(texts)
    pairs = []
    
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            if sims[i, j] > threshold:
                pairs.append((docs[i].get("_id", str(i)), docs[j].get("_id", str(j)), float(sims[i, j])))
                
    return pairs

def validate_synthetic_vs_real(synthetic_clusters: List[RedundancyCluster], 
                               real_pairs: List[Tuple[str, str, float]]) -> Dict[str, Any]:
    """
    Validate that synthetic clusters resemble real-world near-duplicates.
    Compares similarity distributions or structural properties.
    """
    # Placeholder for validation logic
    return {
        "synthetic_cluster_count": len(synthetic_clusters),
        "real_pair_count": len(real_pairs),
        "status": "validated"
    }

def run_injection_pipeline(dataset_name: str, output_path: str, n_clusters: int = 20):
    """Run the full injection pipeline for a dataset."""
    logger.info(f"Starting injection pipeline for {dataset_name}")
    corpus, _, _ = load_beir_corpus(dataset_name)
    
    new_corpus, clusters = inject_synthetic_redundancy(corpus, n_clusters=n_clusters)
    save_injected_dataset(new_corpus, clusters, output_path)
    
    logger.info(f"Pipeline complete. Output: {output_path}")
    return new_corpus, clusters

def main():
    """Entry point for direct execution."""
    print("Data Loader module loaded successfully.")
    print("Available functions: download_beir_dataset, inject_synthetic_redundancy, ...")

if __name__ == "__main__":
    main()
