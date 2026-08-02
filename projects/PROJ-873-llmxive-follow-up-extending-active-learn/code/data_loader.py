"""
Data loading and redundancy injection module for llmXive.
Handles BEIR dataset fetching, synthetic redundancy injection,
and validation of injected similarity thresholds.
"""

import os
import json
import hashlib
import logging
import zipfile
import io
import random
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, field, asdict

# Third-party imports
from beir import util
from beir.datasets.data_loader import GenericDataLoader
import nltk
from nltk.corpus import wordnet
import numpy as np
from sentence_transformers import SentenceTransformer

# Local imports
from config import get_config

# Ensure NLTK resources are available
try:
    wordnet.synsets("test")
except LookupError:
    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
SIMILARITY_THRESHOLD = 0.95
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

@dataclass
class RedundancyCluster:
    """Represents a cluster of near-duplicate passages."""
    cluster_id: int
    seed_doc_id: str
    seed_text: str
    member_doc_ids: List[str] = field(default_factory=list)
    member_texts: List[str] = field(default_factory=list)
    avg_similarity: float = 0.0

@dataclass
class DataInjectionError(Exception):
    """Custom exception for data injection failures."""
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        return f"DataInjectionError: {self.message} - Details: {self.details}"

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_beir_dataset(dataset_name: str, out_dir: str = "beir_data") -> str:
    """Download and unzip a BEIR dataset."""
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    data_path = util.download_and_unzip(url, out_dir)
    logger.info(f"Downloaded {dataset_name} to {data_path}")
    return data_path

def load_beir_corpus(data_path: str, split: str = "test") -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Dict[str, int]]]:
    """Load BEIR corpus, queries, and qrels."""
    loader = GenericDataLoader(data_path)
    corpus, queries, qrels = loader.load(split=split)
    return corpus, queries, qrels

def fetch_beir_datasets(datasets: List[str] = ["nfcorpus", "scifact"]) -> Dict[str, Dict[str, Any]]:
    """Fetch multiple BEIR datasets and return as a structured dict."""
    results = {}
    for dataset_name in datasets:
        try:
            data_path = download_beir_dataset(dataset_name)
            corpus, queries, qrels = load_beir_corpus(data_path)
            results[dataset_name] = {
                "corpus": corpus,
                "queries": queries,
                "qrels": qrels,
                "path": data_path
            }
            logger.info(f"Loaded {dataset_name}: {len(corpus)} docs, {len(queries)} queries")
        except Exception as e:
            logger.error(f"Failed to load {dataset_name}: {e}")
            raise
    return results

def fetch_nfcorpus_and_scifact() -> Dict[str, Dict[str, Any]]:
    """Convenience wrapper for fetching nfcorpus and scifact."""
    return fetch_beir_datasets(["nfcorpus", "scifact"])

def fetch_trec_covid() -> Dict[str, Any]:
    """Fetch trec-covid dataset specifically for FR-009 validation."""
    return fetch_beir_datasets(["trec-covid"])["trec-covid"]

def get_synonyms(word: str) -> List[str]:
    """Get synonyms for a word using WordNet."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower().replace("_", " "))
    synonyms.discard(word.lower())
    return list(synonyms)

def inject_synonym_replacement(text: str, replacement_prob: float = 0.3) -> str:
    """Replace words in text with synonyms to create near-duplicates."""
    words = text.split()
    new_words = []
    for word in words:
        if random.random() < replacement_prob:
            synonyms = get_synonyms(word)
            if synonyms:
                new_words.append(random.choice(synonyms))
            else:
                new_words.append(word)
        else:
            new_words.append(word)
    return " ".join(new_words)

def inject_sentence_shuffle(text: str) -> str:
    """Shuffle sentences in text to create near-duplicates."""
    sentences = text.split(". ")
    if len(sentences) > 1:
        shuffled = sentences.copy()
        random.shuffle(shuffled)
        return ". ".join(shuffled)
    return text

def calculate_embedding_similarity(text1: str, text2: str, model: SentenceTransformer) -> float:
    """Calculate cosine similarity between two texts using embeddings."""
    embeddings = model.encode([text1, text2], convert_to_numpy=True)
    similarity = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
    return float(similarity)

def create_redundancy_clusters(
    corpus: Dict[str, Any],
    qrels: Dict[str, Dict[str, int]],
    cluster_size: int = 3,
    injection_method: str = "synonym"
) -> List[RedundancyCluster]:
    """Create clusters of near-duplicate passages from the corpus."""
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    doc_ids = list(corpus.keys())
    clusters = []
    cluster_id = 0

    # Select a subset of documents to inject redundancy into
    # Use a deterministic seed for reproducibility
    random.seed(42)
    sample_docs = random.sample(doc_ids, min(100, len(doc_ids)))

    for seed_doc_id in sample_docs:
        seed_text = corpus[seed_doc_id]["text"] if isinstance(corpus[seed_doc_id], dict) else str(corpus[seed_doc_id])
        members = [seed_doc_id]
        member_texts = [seed_text]

        # Generate synthetic duplicates
        for _ in range(cluster_size - 1):
            if injection_method == "synonym":
                new_text = inject_synonym_replacement(seed_text, replacement_prob=0.3)
            elif injection_method == "shuffle":
                new_text = inject_sentence_shuffle(seed_text)
            else:
                raise ValueError(f"Unknown injection method: {injection_method}")

            # Create a new doc_id for the synthetic duplicate
            new_doc_id = f"{seed_doc_id}_syn_{len(members)}"
            members.append(new_doc_id)
            member_texts.append(new_text)

            # Add to corpus (in-memory)
            corpus[new_doc_id] = {"text": new_text}

        # Calculate average similarity within the cluster
        similarities = []
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                sim = calculate_embedding_similarity(member_texts[i], member_texts[j], model)
                similarities.append(sim)

        avg_sim = np.mean(similarities) if similarities else 0.0

        cluster = RedundancyCluster(
            cluster_id=cluster_id,
            seed_doc_id=seed_doc_id,
            seed_text=seed_text,
            member_doc_ids=members,
            member_texts=member_texts,
            avg_similarity=avg_sim
        )
        clusters.append(cluster)
        cluster_id += 1

    return clusters

def validate_injected_similarity(clusters: List[RedundancyCluster]) -> bool:
    """
    Validate that injected redundancy achieves target similarity > 0.95.
    Raises DataInjectionError if validation fails.
    """
    if not clusters:
        raise DataInjectionError(
            message="No clusters to validate",
            details={"reason": "Empty cluster list"}
        )

    failed_clusters = []
    for cluster in clusters:
        if cluster.avg_similarity < SIMILARITY_THRESHOLD:
            failed_clusters.append({
                "cluster_id": cluster.cluster_id,
                "seed_doc_id": cluster.seed_doc_id,
                "avg_similarity": cluster.avg_similarity,
                "threshold": SIMILARITY_THRESHOLD
            })

    if failed_clusters:
        details = {
            "total_clusters": len(clusters),
            "failed_clusters": len(failed_clusters),
            "failure_rate": len(failed_clusters) / len(clusters),
            "sample_failures": failed_clusters[:5]  # Show first 5 failures
        }
        raise DataInjectionError(
            message=f"Injected similarity validation failed: {len(failed_clusters)} clusters below threshold {SIMILARITY_THRESHOLD}",
            details=details
        )

    logger.info(f"All {len(clusters)} clusters passed similarity validation (avg > {SIMILARITY_THRESHOLD})")
    return True

def save_injected_dataset(clusters: List[RedundancyCluster], output_path: str):
    """Save injected dataset clusters to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    data = [asdict(cluster) for cluster in clusters]
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved injected dataset to {output_path}")

def load_injected_dataset(input_path: str) -> List[RedundancyCluster]:
    """Load injected dataset clusters from JSON file."""
    with open(input_path, "r") as f:
        data = json.load(f)
    return [RedundancyCluster(**item) for item in data]

def prepare_injected_datasets(datasets: Dict[str, Dict[str, Any]], output_dir: str = "data/processed") -> Dict[str, str]:
    """
    Prepare injected datasets for nfcorpus and scifact.
    Returns paths to saved JSON files.
    """
    output_paths = {}
    os.makedirs(output_dir, exist_ok=True)

    for dataset_name, dataset_data in datasets.items():
        logger.info(f"Creating redundancy clusters for {dataset_name}")
        clusters = create_redundancy_clusters(
            corpus=dataset_data["corpus"],
            qrels=dataset_data["qrels"],
            cluster_size=3,
            injection_method="synonym"
        )

        # Validate similarity before saving
        validate_injected_similarity(clusters)

        output_path = os.path.join(output_dir, f"injected_{dataset_name}.json")
        save_injected_dataset(clusters, output_path)
        output_paths[dataset_name] = output_path

    # Also save a combined file
    all_clusters = []
    for dataset_name, dataset_data in datasets.items():
        clusters = create_redundancy_clusters(
            corpus=dataset_data["corpus"],
            qrels=dataset_data["qrels"],
            cluster_size=3,
            injection_method="synonym"
        )
        all_clusters.extend(clusters)

    combined_path = os.path.join(output_dir, "injected_datasets.json")
    save_injected_dataset(all_clusters, combined_path)
    output_paths["combined"] = combined_path

    return output_paths

def validate_redundancy_clusters_on_trec_covid(
    trec_covid_data: Dict[str, Any],
    output_path: str = "data/results/trec_covid_validation.json"
) -> Dict[str, Any]:
    """
    Validate redundancy clusters on trec-covid dataset.
    Implements the "paraphrasing fails to generate sufficient semantic similarity"
    edge case handling: if injected similarity < 0.95, raise DataInjectionError.
    """
    logger.info("Validating redundancy clusters on trec-covid dataset")

    corpus = trec_covid_data["corpus"]
    qrels = trec_covid_data["qrels"]

    # Create clusters
    clusters = create_redundancy_clusters(
        corpus=corpus,
        qrels=qrels,
        cluster_size=3,
        injection_method="synonym"
    )

    result = {
        "dataset": "trec-covid",
        "injection_success": False,
        "avg_similarity": 0.0,
        "clusters_validated": len(clusters),
        "failed_clusters": []
    }

    if not clusters:
        raise DataInjectionError(
            message="No clusters created for trec-covid",
            details={"reason": "Empty corpus or qrels"}
        )

    # Calculate overall average similarity
    all_similarities = [cluster.avg_similarity for cluster in clusters]
    result["avg_similarity"] = float(np.mean(all_similarities))

    # Validate each cluster - THIS IS THE CORE OF T037
    # If any cluster fails the threshold, we raise DataInjectionError
    failed_count = 0
    for cluster in clusters:
        if cluster.avg_similarity < SIMILARITY_THRESHOLD:
            failed_count += 1
            result["failed_clusters"].append({
                "cluster_id": cluster.cluster_id,
                "avg_similarity": cluster.avg_similarity
            })

    if failed_count > 0:
        # Explicit failure mode handling: raise error instead of proceeding
        raise DataInjectionError(
            message=f"TREC-COVID injection validation failed: {failed_count}/{len(clusters)} clusters below threshold {SIMILARITY_THRESHOLD}",
            details={
                "total_clusters": len(clusters),
                "failed_clusters": failed_count,
                "avg_similarity": result["avg_similarity"],
                "threshold": SIMILARITY_THRESHOLD
            }
        )

    result["injection_success"] = True
    result["failed_clusters"] = []

    # Save result
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"TREC-COVID validation successful: {result}")
    return result

def main():
    """Main entry point for data_loader CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="BEIR Data Loader and Redundancy Injector")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Prepare command
    prepare_parser = subparsers.add_parser("prepare", help="Prepare injected datasets")
    prepare_parser.add_argument("--datasets", nargs="+", default=["nfcorpus", "scifact"],
                                help="Datasets to prepare")
    prepare_parser.add_argument("--output-dir", default="data/processed",
                                help="Output directory for injected datasets")

    # Validate TREC-COVID command
    validate_parser = subparsers.add_parser("validate_trec_covid", help="Validate redundancy on TREC-COVID")
    validate_parser.add_argument("--output", default="data/results/trec_covid_validation.json",
                                 help="Output path for validation result")

    args = parser.parse_args()

    if args.command == "prepare":
        logger.info(f"Preparing injected datasets: {args.datasets}")
        datasets = fetch_beir_datasets(args.datasets)
        output_paths = prepare_injected_datasets(datasets, args.output_dir)
        logger.info(f"Prepared datasets saved to: {output_paths}")

    elif args.command == "validate_trec_covid":
        logger.info("Validating TREC-COVID dataset")
        trec_covid_data = fetch_trec_covid()
        result = validate_redundancy_clusters_on_trec_covid(trec_covid_data, args.output)
        logger.info(f"Validation result: {result}")

    else:
        parser.print_help()
        exit(1)

if __name__ == "__main__":
    main()