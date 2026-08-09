import os
import sys
import json
import logging
import zipfile
import io
import random
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import nltk
from nltk.corpus import wordnet
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Ensure NLTK data is available
try:
    wordnet.synsets('good')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Initialize logging
logger = logging.getLogger(__name__)

@dataclass
class RedundancyCluster:
    id: str
    members: List[str]
    original_doc_id: str
    injected_docs: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class InjectedDataset:
    name: str
    clusters: List[RedundancyCluster]
    original_corpus_size: int
    injected_corpus_size: int
    achieved_similarity: float
    validation_status: str
    retry_count: int

class DataInjectionError(Exception):
    pass

class DataInjectionFailureError(Exception):
    pass

class DataInjectionWarning(Exception):
    """Raised when injection fails to meet threshold but pipeline proceeds with achieved data."""
    pass

def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_beir_dataset(dataset_name: str, data_path: str = "beir_data") -> str:
    from beir import util
    from beir.datasets.data_loader import GenericDataLoader

    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    full_path = util.download_and_unzip(url, data_path)
    return full_path

def load_beir_corpus(dataset_name: str, data_path: str = "beir_data") -> Tuple[Dict[str, Dict[str, str]], Dict[str, str], Dict[str, Dict[str, int]]]:
    from beir.datasets.data_loader import GenericDataLoader

    full_path = os.path.join(data_path, dataset_name)
    loader = GenericDataLoader(full_path)
    corpus, queries, qrels = loader.load(split="test")
    return corpus, queries, qrels

def fetch_beir_datasets(dataset_names: List[str], data_path: str = "beir_data") -> Dict[str, Dict[str, Any]]:
    datasets = {}
    for name in dataset_names:
        try:
            corpus, queries, qrels = load_beir_corpus(name, data_path)
            datasets[name] = {
                "corpus": corpus,
                "queries": queries,
                "qrels": qrels
            }
        except Exception as e:
            logger.error(f"Failed to load dataset {name}: {e}")
            raise
    return datasets

def get_synonyms(word: str, max_synonyms: int = 5) -> List[str]:
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            if lemma.name() != word:
                synonyms.add(lemma.name().replace("_", " "))
    return list(synonyms)[:max_synonyms]

def paraphrase_text(text: str, intensity: float = 0.3) -> str:
    words = text.split()
    paraphrased = []
    for word in words:
        if random.random() < intensity:
            syns = get_synonyms(word)
            if syns:
                paraphrased.append(random.choice(syns))
            else:
                paraphrased.append(word)
        else:
            paraphrased.append(word)
    return " ".join(paraphrased)

def calculate_embedding_similarity(text1: str, text2: str, model: SentenceTransformer) -> float:
    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(sim)

def inject_redundancy(
    corpus: Dict[str, Dict[str, str]],
    dataset_name: str,
    num_clusters: int = 10,
    members_per_cluster: int = 5,
    target_similarity: float = 0.95,
    max_retries: int = 3,
    min_intensity: float = 0.2,
    max_intensity: float = 0.8
) -> Tuple[Dict[str, Dict[str, str]], List[RedundancyCluster], float, int]:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    new_corpus = dict(corpus)
    clusters = []
    achieved_similarity = 0.0
    retry_count = 0

    # Select random base documents to create clusters from
    doc_ids = list(corpus.keys())
    if len(doc_ids) < num_clusters:
        raise DataInjectionError("Not enough documents in corpus to create requested clusters.")

    base_docs = random.sample(doc_ids, num_clusters)

    for i, base_id in enumerate(base_docs):
        base_doc = corpus[base_id]
        base_text = base_doc['text']
        cluster_id = f"cluster_{dataset_name}_{i}"
        injected_members = []

        current_intensity = min_intensity
        best_injected_docs = []
        best_sim = 0.0

        # Retry logic with increasing intensity
        for attempt in range(max_retries):
            injected_docs = []
            sim_scores = []

            for j in range(members_per_cluster):
                # Generate paraphrase with current intensity
                new_text = paraphrase_text(base_text, intensity=current_intensity)
                new_id = f"{base_id}_inj_{j}_{attempt}"
                new_doc = {
                    'text': new_text,
                    'title': base_doc.get('title', '')
                }
                new_corpus[new_id] = new_doc
                injected_docs.append({
                    'id': new_id,
                    'text': new_text,
                    'original_id': base_id
                })

                # Calculate similarity
                sim = calculate_embedding_similarity(base_text, new_text, model)
                sim_scores.append(sim)

            avg_sim = np.mean(sim_scores)
            if avg_sim > best_sim:
                best_sim = avg_sim
                best_injected_docs = injected_docs

            if avg_sim >= target_similarity:
                achieved_similarity = avg_sim
                injected_members = best_injected_docs
                break

            # Increase intensity for next retry
            current_intensity = min(max_intensity, current_intensity + 0.15)
            retry_count += 1

        # If we couldn't reach target, use the best we got
        if achieved_similarity < target_similarity:
            achieved_similarity = best_sim
            injected_members = best_injected_docs

        cluster = RedundancyCluster(
            id=cluster_id,
            members=[m['id'] for m in injected_members],
            original_doc_id=base_id,
            injected_docs=injected_members
        )
        clusters.append(cluster)

    return new_corpus, clusters, achieved_similarity, retry_count

def prepare_injected_datasets(
    datasets: Dict[str, Dict[str, Any]],
    output_path: str = "data/processed/injected_datasets.json",
    target_similarity: float = 0.95,
    max_retries: int = 3
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    injected_data = {
        "datasets": []
    }

    for name, data in datasets.items():
        corpus = data['corpus']
        logger.info(f"Injecting redundancy into {name}...")

        new_corpus, clusters, achieved_sim, retries = inject_redundancy(
            corpus,
            name,
            num_clusters=5,  # Reduced for speed
            members_per_cluster=3,
            target_similarity=target_similarity,
            max_retries=max_retries
        )

        dataset_entry = {
            "name": name,
            "clusters": [asdict(c) for c in clusters],
            "original_corpus_size": len(corpus),
            "injected_corpus_size": len(new_corpus),
            "achieved_similarity": achieved_sim,
            "validation_status": "achieved" if achieved_sim >= target_similarity else "below_target",
            "retry_count": retries,
            "message": f"Achieved similarity {achieved_sim:.4f} (target: {target_similarity})"
        }

        # Handle edge case: if similarity is below target, log warning but proceed
        if achieved_sim < target_similarity:
            logger.warning(f"DataInjectionWarning: {name} achieved similarity {achieved_sim:.4f} < {target_similarity}. Proceeding with achieved data.")
            # We do NOT raise an error, per T037/T043/T058 requirements
            # The pipeline continues with the achieved similarity level

        injected_data["datasets"].append(dataset_entry)

        # Save the new corpus for this dataset
        corpus_output_path = output_path.replace("injected_datasets.json", f"corpus_{name}.json")
        with open(corpus_output_path, 'w', encoding='utf-8') as f:
            json.dump(new_corpus, f, indent=2)

    # Write the main injected datasets summary
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(injected_data, f, indent=2)

    logger.info(f"Injected datasets saved to {output_path}")

def load_injected_dataset(path: str = "data/processed/injected_datasets.json") -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Injected dataset file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger.info("Starting data injection pipeline...")

    try:
        # Fetch real BEIR datasets
        datasets = fetch_beir_datasets(["scifact", "nfcorpus"])
        logger.info(f"Loaded {len(datasets)} datasets")

        # Prepare injected datasets with redundancy
        prepare_injected_datasets(datasets)

        logger.info("Data injection completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()