import os
import json
import hashlib
import logging
import zipfile
import io
import random
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import wordnet
import pandas as pd
from beir import util
from beir.datasets.data_loader import GenericDataLoader
from config import get_config

# Ensure NLTK data is available
try:
    wordnet.all_synsets('n')
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    nltk.download('averaged_perceptron_tagger', quiet=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RedundancyCluster:
    cluster_id: str
    original_doc_id: str
    original_text: str
    injected_docs: List[Dict[str, Any]]
    avg_similarity: float

class DataInjectionError(Exception):
    """Raised when data injection fails to meet semantic similarity thresholds."""
    pass

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_beir_dataset(dataset_name: str) -> str:
    """Download and unzip a BEIR dataset."""
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    out_dir = os.path.join(get_config().data_dir, "raw", dataset_name)
    os.makedirs(out_dir, exist_ok=True)
    data_path = util.download_and_unzip(url, out_dir)
    return data_path

def load_beir_corpus(dataset_name: str, split: str = "test") -> Tuple[Dict, Dict, Dict]:
    """Load BEIR corpus, queries, and qrels."""
    data_path = download_beir_dataset(dataset_name)
    data_folder = os.path.join(data_path, dataset_name) if os.path.isdir(os.path.join(data_path, dataset_name)) else data_path
    corpus, queries, qrels = GenericDataLoader(data_folder=data_folder).load(split=split)
    return corpus, queries, qrels

def fetch_beir_datasets(datasets: List[str]) -> List[Dict[str, Any]]:
    """Fetch multiple BEIR datasets and return a list of records."""
    records = []
    for ds in datasets:
        try:
            corpus, queries, qrels = load_beir_corpus(ds, split="test")
            for qid, rels in qrels.items():
                query_obj = queries[qid]
                query_text = query_obj["text"] if isinstance(query_obj, dict) else query_obj
                for docid, score in rels.items():
                    doc_obj = corpus[docid]
                    doc_text = doc_obj["text"] if isinstance(doc_obj, dict) else doc_obj
                    records.append({
                        "query_id": qid,
                        "query_text": query_text,
                        "doc_id": docid,
                        "doc_text": doc_text,
                        "relevance_score": score,
                        "split": "test",
                        "dataset": ds
                    })
        except Exception as e:
            logger.error(f"Failed to load dataset {ds}: {e}")
            raise
    return records

def fetch_nfcorpus_and_scifact() -> List[Dict[str, Any]]:
    """Fetch nfcorpus and scifact datasets."""
    return fetch_beir_datasets(["nfcorpus", "scifact"])

def fetch_trec_covid() -> List[Dict[str, Any]]:
    """Fetch trec-covid dataset."""
    return fetch_beir_datasets(["trec-covid"])

def get_synonyms(word: str) -> List[str]:
    """Get synonyms for a word using WordNet."""
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", " "))
    return list(synonyms)

def inject_synonym_replacement(text: str, replacement_rate: float = 0.3) -> str:
    """Inject redundancy by replacing words with synonyms."""
    words = text.split()
    new_words = []
    for word in words:
        if random.random() < replacement_rate:
            synonyms = get_synonyms(word)
            if synonyms:
                new_words.append(random.choice(synonyms))
            else:
                new_words.append(word)
        else:
            new_words.append(word)
    return " ".join(new_words)

def inject_sentence_shuffle(text: str) -> str:
    """Inject redundancy by shuffling sentences."""
    sentences = text.split(". ")
    if len(sentences) > 1:
        random.shuffle(sentences)
        return ". ".join(sentences)
    return text

def calculate_embedding_similarity(text1: str, text2: str, model: SentenceTransformer) -> float:
    """Calculate cosine similarity between two texts using embeddings."""
    embeddings = model.encode([text1, text2], convert_to_tensor=False)
    similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return similarity

def create_redundancy_clusters(
    documents: List[Dict[str, Any]],
    model: SentenceTransformer,
    target_similarity: float = 0.95,
    cluster_size: int = 3
) -> List[RedundancyCluster]:
    """
    Create clusters of near-duplicate documents by injecting paraphrases.
    
    Raises DataInjectionError if the injected similarity is below the target threshold.
    """
    clusters = []
    processed_ids = set()

    for doc in documents:
        if doc["doc_id"] in processed_ids:
            continue

        original_text = doc["doc_text"]
        injected_docs = []

        for i in range(cluster_size - 1):
            # Try multiple injection strategies if the first fails
            injected_text = None
            strategies = [
                lambda t: inject_synonym_replacement(t, 0.3),
                lambda t: inject_synonym_replacement(t, 0.5),
                lambda t: inject_sentence_shuffle(t),
                lambda t: inject_synonym_replacement(t, 0.7)
            ]

            for strategy in strategies:
                candidate = strategy(original_text)
                sim = calculate_embedding_similarity(original_text, candidate, model)
                if sim >= target_similarity:
                    injected_text = candidate
                    break

            if injected_text is None:
                # Final attempt with maximum synonym replacement
                candidate = inject_synonym_replacement(original_text, 0.9)
                sim = calculate_embedding_similarity(original_text, candidate, model)
                if sim < target_similarity:
                    # FAIL LOUDLY: Raise specific error with details
                    raise DataInjectionError(
                        f"Injected similarity {sim:.4f} is below threshold {target_similarity}. "
                        f"Paraphrasing failed to generate sufficient semantic similarity for document {doc['doc_id']}."
                    )
                injected_text = candidate

            injected_docs.append({
                "doc_id": f"{doc['doc_id']}_injected_{i}",
                "doc_text": injected_text,
                "original_id": doc["doc_id"]
            })

        # Calculate average similarity for the cluster
        similarities = []
        for injected in injected_docs:
            sim = calculate_embedding_similarity(original_text, injected["doc_text"], model)
            similarities.append(sim)
        
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.0

        cluster = RedundancyCluster(
            cluster_id=f"cluster_{doc['doc_id']}",
            original_doc_id=doc["doc_id"],
            original_text=original_text,
            injected_docs=injected_docs,
            avg_similarity=avg_similarity
        )
        clusters.append(cluster)
        processed_ids.add(doc["doc_id"])

        # Log progress
        if len(clusters) % 100 == 0:
            logger.info(f"Created {len(clusters)} clusters, avg similarity: {avg_similarity:.4f}")

    return clusters

def load_injected_dataset(path: str) -> List[Dict[str, Any]]:
    """Load an injected dataset from a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def save_injected_dataset(clusters: List[RedundancyCluster], path: str) -> None:
    """Save injected dataset to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {
        "clusters": [asdict(c) for c in clusters]
    }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def prepare_injected_datasets(
    datasets: List[str],
    output_path: str,
    target_similarity: float = 0.95,
    cluster_size: int = 3
) -> List[RedundancyCluster]:
    """
    Prepare injected datasets for specified BEIR datasets.
    
    Raises DataInjectionError if any dataset fails to meet the similarity threshold.
    """
    logger.info(f"Preparing injected datasets for {datasets}")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    
    all_clusters = []
    
    for dataset in datasets:
        try:
            logger.info(f"Processing dataset: {dataset}")
            corpus, queries, qrels = load_beir_corpus(dataset, split="test")
            
            # Convert to list of documents
            documents = []
            for docid, doc_obj in corpus.items():
                doc_text = doc_obj["text"] if isinstance(doc_obj, dict) else doc_obj
                documents.append({
                    "doc_id": docid,
                    "doc_text": doc_text,
                    "dataset": dataset
                })
            
            # Create redundancy clusters
            clusters = create_redundancy_clusters(
                documents, 
                model, 
                target_similarity=target_similarity, 
                cluster_size=cluster_size
            )
            all_clusters.extend(clusters)
            logger.info(f"Successfully created {len(clusters)} clusters for {dataset}")
            
        except DataInjectionError as e:
            logger.error(f"Data injection failed for {dataset}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to process dataset {dataset}: {e}")
            raise

    # Save the result
    save_injected_dataset(all_clusters, output_path)
    logger.info(f"Saved injected dataset to {output_path}")
    
    # Validate the result
    loaded = load_injected_dataset(output_path)
    if not loaded or len(loaded.get("clusters", [])) == 0:
        raise RuntimeError("Injected dataset is empty or invalid")
        
    return all_clusters

def validate_redundancy_clusters_on_trec_covid(
    clusters: List[RedundancyCluster],
    target_similarity: float = 0.95
) -> Dict[str, Any]:
    """Validate that redundancy clusters on trec-covid meet the similarity threshold."""
    trec_covid_clusters = [c for c in clusters if any(d.get("dataset") == "trec-covid" for d in [c])]
    
    if not trec_covid_clusters:
        return {"status": "FAIL", "reason": "No trec-covid clusters found"}
    
    failed_clusters = []
    for cluster in trec_covid_clusters:
        if cluster.avg_similarity < target_similarity:
            failed_clusters.append({
                "cluster_id": cluster.cluster_id,
                "avg_similarity": cluster.avg_similarity
            })
    
    if failed_clusters:
        return {
            "status": "FAIL",
            "reason": f"{len(failed_clusters)} clusters below threshold",
            "failed_clusters": failed_clusters
        }
    
    return {"status": "PASS", "total_clusters": len(trec_covid_clusters)}

def main():
    """Main entry point for data loader script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="BEIR Data Loader with Redundancy Injection")
    parser.add_argument("--prepare", action="store_true", help="Prepare injected datasets")
    parser.add_argument("--datasets", nargs="+", default=["nfcorpus", "scifact"], help="Datasets to process")
    parser.add_argument("--output", type=str, help="Output path for injected dataset")
    parser.add_argument("--similarity", type=float, default=0.95, help="Target similarity threshold")
    parser.add_argument("--cluster-size", type=int, default=3, help="Size of redundancy clusters")
    
    args = parser.parse_args()
    
    if args.prepare:
        config = get_config()
        output_path = args.output or os.path.join(config.data_dir, "processed", "injected_datasets.json")
        
        try:
            clusters = prepare_injected_datasets(
                args.datasets,
                output_path,
                target_similarity=args.similarity,
                cluster_size=args.cluster_size
            )
            logger.info(f"Successfully prepared {len(clusters)} clusters")
        except DataInjectionError as e:
            logger.error(f"Data injection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

if __name__ == "__main__":
    main()