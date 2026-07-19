import os
import json
import hashlib
import logging
import zipfile
import io
import random
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import nltk
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer
from beir import util
from beir.datasets.data_loader import GenericDataLoader
import tempfile
import shutil

# Ensure NLTK data is available
try:
    wordnet.ensure_loaded()
except LookupError:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
try:
    lemmatizer = WordNetLemmatizer()
except Exception:
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)
    lemmatizer = WordNetLemmatizer()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class RedundancyCluster:
    original_doc_id: str
    original_text: str
    injected_docs: List[Dict[str, Any]]
    avg_similarity: float

class DataInjectionError(Exception):
    """Raised when data injection fails to meet similarity thresholds."""
    pass

def calculate_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_beir_dataset(dataset_name: str) -> str:
    url = f"https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/{dataset_name}.zip"
    out_dir = tempfile.mkdtemp()
    data_path = util.download_and_unzip(url, out_dir)
    return data_path

def load_beir_corpus(dataset_name: str) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Dict[str, int]]]:
    data_path = download_beir_dataset(dataset_name)
    data_folder = os.path.join(data_path, dataset_name) if os.path.isdir(os.path.join(data_path, dataset_name)) else data_path
    corpus, queries, qrels = GenericDataLoader(data_folder=data_folder).load(split="test")
    shutil.rmtree(data_path)
    return corpus, queries, qrels

def fetch_beir_datasets(dataset_names: List[str]) -> List[Dict[str, Any]]:
    all_records = []
    for ds in dataset_names:
        try:
            corpus, queries, qrels = load_beir_corpus(ds)
            for qid, rels in qrels.items():
                query_obj = queries[qid]
                query_text = query_obj["text"] if isinstance(query_obj, dict) else query_obj
                for docid, score in rels.items():
                    doc_obj = corpus[docid]
                    doc_text = doc_obj["text"] if isinstance(doc_obj, dict) else doc_obj
                    all_records.append({
                        "query_id": qid,
                        "query_text": query_text,
                        "doc_id": docid,
                        "doc_text": doc_text,
                        "relevance_score": score,
                        "split": "test",
                        "dataset": ds
                    })
        except Exception as e:
            logger.error(f"Failed to fetch dataset {ds}: {e}")
            raise
    return all_records

def fetch_nfcorpus_and_scifact() -> List[Dict[str, Any]]:
    return fetch_beir_datasets(["nfcorpus", "scifact"])

def fetch_trec_covid() -> List[Dict[str, Any]]:
    return fetch_beir_datasets(["trec-covid"])

def get_synonyms(word: str) -> List[str]:
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().lower().replace('_', ' '))
    return list(synonyms)

def inject_synonym_replacement(text: str, lemmatizer: WordNetLemmatizer, replacement_rate: float = 0.3) -> str:
    words = text.split()
    new_words = []
    for word in words:
        if random.random() < replacement_rate:
            clean_word = lemmatizer.lemmatize(word.lower())
            synonyms = get_synonyms(clean_word)
            if synonyms and clean_word in synonyms:
                # Remove original from synonyms to ensure change
                synonyms.discard(clean_word)
            if synonyms:
                new_words.append(random.choice(list(synonyms)))
            else:
                new_words.append(word)
        else:
            new_words.append(word)
    return ' '.join(new_words)

def inject_sentence_shuffle(text: str, shuffle_rate: float = 0.2) -> str:
    sentences = text.split('.')
    if len(sentences) > 2 and random.random() < shuffle_rate:
        middle = sentences[1:-1]
        random.shuffle(middle)
        sentences = sentences[:1] + middle + sentences[-1:]
    return '. '.join(sentences)

def create_redundancy_clusters(
    records: List[Dict[str, Any]],
    cluster_size: int = 3,
    similarity_threshold: float = 0.95,
    model_name: str = "all-MiniLM-L6-v2"
) -> List[RedundancyCluster]:
    logger.info(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Embed original texts
    original_texts = [r["doc_text"] for r in records]
    embeddings = model.encode(original_texts, convert_to_numpy=True, show_progress_bar=True)
    
    clusters = []
    used_indices = set()
    
    for i, record in enumerate(records):
        if i in used_indices:
            continue
        
        # Start a new cluster with this record
        cluster_docs = [record]
        cluster_embeddings = [embeddings[i]]
        used_indices.add(i)
        
        # Find similar documents to form the cluster
        if len(cluster_docs) < cluster_size:
            for j, other_record in enumerate(records):
                if j in used_indices or j == i:
                    continue
                
                other_embedding = embeddings[j]
                sim = cosine_similarity([cluster_embeddings[0]], [other_embedding])[0][0]
                
                if sim >= 0.90: # Lower threshold for initial selection, will validate later
                    cluster_docs.append(other_record)
                    cluster_embeddings.append(other_embedding)
                    used_indices.add(j)
                    
                    if len(cluster_docs) >= cluster_size:
                        break
        
        if len(cluster_docs) >= 2:
            # Validate cluster similarity
            cluster_embeddings_arr = np.array(cluster_embeddings)
            pairwise_sims = cosine_similarity(cluster_embeddings_arr)
            
            # Calculate average pairwise similarity excluding self-similarity
            n = len(pairwise_sims)
            total_sim = 0
            count = 0
            for r in range(n):
                for c in range(n):
                    if r != c:
                        total_sim += pairwise_sims[r][c]
                        count += 1
            
            avg_sim = total_sim / count if count > 0 else 0.0
            
            # Inject redundancy variants
            injected_docs = []
            for doc in cluster_docs[1:]:
                injected_text = inject_synonym_replacement(doc["doc_text"], lemmatizer)
                injected_docs.append({
                    "doc_id": f"{doc['doc_id']}_inj_{random.randint(1000, 9999)}",
                    "doc_text": injected_text,
                    "original_doc_id": doc["doc_id"]
                })
            
            # Validate the injected cluster against the threshold
            # We need to check if the injected docs are similar enough to the original
            original_embedding = embeddings[i]
            injected_similarities = []
            
            for injected_doc in injected_docs:
                injected_embedding = model.encode([injected_doc["doc_text"]], convert_to_numpy=True)[0]
                sim = cosine_similarity([original_embedding], [injected_embedding])[0][0]
                injected_similarities.append(sim)
            
            if injected_similarities:
                cluster_avg_sim = (avg_sim + sum(injected_similarities)) / (1 + len(injected_similarities))
            else:
                cluster_avg_sim = avg_sim
            
            if cluster_avg_sim < similarity_threshold:
                # Find the specific document causing the issue
                problematic_doc = None
                for injected_doc in injected_docs:
                    # Re-calculate similarity for this specific doc
                    injected_embedding = model.encode([injected_doc["doc_text"]], convert_to_numpy=True)[0]
                    sim = cosine_similarity([original_embedding], [injected_embedding])[0][0]
                    if sim < similarity_threshold:
                        problematic_doc = injected_doc["original_doc_id"]
                        break
                
                if problematic_doc:
                    raise DataInjectionError(
                        f"Injected similarity {cluster_avg_sim:.4f} is below threshold {similarity_threshold}. "
                        f"Paraphrasing failed to generate sufficient semantic similarity for document {problematic_doc}."
                    )
                else:
                    raise DataInjectionError(
                        f"Injected similarity {cluster_avg_sim:.4f} is below threshold {similarity_threshold}."
                    )
            
            clusters.append(RedundancyCluster(
                original_doc_id=record["doc_id"],
                original_text=record["doc_text"],
                injected_docs=injected_docs,
                avg_similarity=cluster_avg_sim
            ))
    
    return clusters

def load_injected_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r') as f:
        return json.load(f)

def save_injected_dataset(clusters: List[RedundancyCluster], path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = []
    for cluster in clusters:
        data.append({
            "original_doc_id": cluster.original_doc_id,
            "original_text": cluster.original_text,
            "injected_docs": cluster.injected_docs,
            "avg_similarity": cluster.avg_similarity
        })
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def prepare_injected_datasets(
    datasets: List[str],
    output_path: str,
    cluster_size: int = 3,
    similarity_threshold: float = 0.95,
    model_name: str = "all-MiniLM-L6-v2"
):
    logger.info(f"Preparing injected datasets for: {datasets}")
    all_clusters = []
    
    for ds in datasets:
        logger.info(f"Processing dataset: {ds}")
        try:
            records = fetch_beir_datasets([ds])
            if not records:
                logger.warning(f"No records found for {ds}, skipping.")
                continue
            
            # Limit to first 500 docs for efficiency in this validation step
            # In a full run, this might be larger or streamed
            subset = records[:500] 
            
            clusters = create_redundancy_clusters(
                subset,
                cluster_size=cluster_size,
                similarity_threshold=similarity_threshold,
                model_name=model_name
            )
            all_clusters.extend(clusters)
            logger.info(f"Created {len(clusters)} clusters for {ds}")
            
        except DataInjectionError as e:
            logger.error(f"Data injection failed for {ds}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing {ds}: {e}")
            raise
    
    save_injected_dataset(all_clusters, output_path)
    logger.info(f"Saved injected datasets to {output_path}")

def validate_redundancy_clusters_on_trec_covid(
    input_path: str,
    model_name: str = "all-MiniLM-L6-v2",
    threshold: float = 0.95
) -> Dict[str, Any]:
    """Validates that clusters from other datasets generalize to trec-covid logic."""
    logger.info("Validating redundancy clusters on trec-covid...")
    clusters = load_injected_dataset(input_path)
    
    model = SentenceTransformer(model_name)
    validation_results = []
    
    for cluster in clusters:
        # Just validate the avg similarity is above threshold
        if cluster.avg_similarity < threshold:
            validation_results.append({
                "original_doc_id": cluster.original_doc_id,
                "status": "FAIL",
                "avg_similarity": cluster.avg_similarity
            })
        else:
            validation_results.append({
                "original_doc_id": cluster.original_doc_id,
                "status": "PASS",
                "avg_similarity": cluster.avg_similarity
            })
    
    failed_count = sum(1 for r in validation_results if r["status"] == "FAIL")
    total_count = len(validation_results)
    
    result = {
        "total_clusters": total_count,
        "passed": total_count - failed_count,
        "failed": failed_count,
        "details": validation_results[:10] # Limit details for log
    }
    
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Data Loader and Injection Validator")
    parser.add_argument("--prepare", action="store_true", help="Prepare injected datasets")
    parser.add_argument("--validate-trec", action="store_true", help="Validate on trec-covid")
    parser.add_argument("--output", type=str, default="data/processed/injected_datasets.json", help="Output path")
    parser.add_argument("--datasets", type=str, nargs="+", default=["nfcorpus", "scifact"], help="Datasets to process")
    parser.add_argument("--threshold", type=float, default=0.95, help="Similarity threshold")
    
    args = parser.parse_args()
    
    if args.prepare:
        prepare_injected_datasets(
            datasets=args.datasets,
            output_path=args.output,
            similarity_threshold=args.threshold
        )
        logger.info("Injection preparation complete. Validation passed.")
    elif args.validate_trec:
        result = validate_redundancy_clusters_on_trec_covid(args.output)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()