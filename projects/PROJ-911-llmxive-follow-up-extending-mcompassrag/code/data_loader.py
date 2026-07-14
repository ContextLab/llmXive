import random
from typing import List, Dict, Any, Tuple
from datasets import load_dataset
from code.config import MAX_DOCS, RANDOM_SEED

def load_hotpotqa_sample() -> List[Dict[str, Any]]:
    """
    Load HotpotQA (fullwiki) and return a deterministic sample of N <= MAX_DOCS.
    Returns a list of documents where each document has 'title', 'text', and 'id'.
    This function loads the TRAIN split, which serves as the training corpus.
    """
    random.seed(RANDOM_SEED)
    # Load the dataset
    dataset = load_dataset("hotpot_qa", "fullwiki", split="train")
    
    # Ensure we do not exceed MAX_DOCS (360)
    sample_size = min(len(dataset), MAX_DOCS)
    indices = random.sample(range(len(dataset)), sample_size)
    
    samples = []
    for idx in indices:
        item = dataset[idx]
        # HotpotQA structure varies; we extract title and context paragraphs
        # We concatenate paragraphs into a single text block for this research task
        title = item.get('title', 'Unknown')
        context = item.get('context', [])
        
        text_parts = []
        for paragraph in context:
            if isinstance(paragraph, dict):
                p_title = paragraph.get('title', '')
                p_text = paragraph.get('paragraph_text', '')
                if p_text:
                    text_parts.append(f"{p_title} {p_text}")
            elif isinstance(paragraph, str):
                text_parts.append(paragraph)
        
        text = "\n".join(text_parts)
        
        samples.append({
            "id": f"hp_{idx}",
            "title": title,
            "text": text,
            "source": "hotpot_qa"
        })
    
    return samples

def load_wikipedia_sample() -> List[Dict[str, Any]]:
    """
    Load Wikipedia 20231001.en and return a deterministic sample of N <= MAX_DOCS.
    Returns a list of documents with 'title', 'text', and 'id'.
    This function loads the TRAIN split, serving as the external corpus for retrieval.
    """
    random.seed(RANDOM_SEED + 1) # Different seed for disjoint sampling
    # Load Wikipedia dataset
    dataset = load_dataset("wikipedia", "20231001.en", split="train")
    
    # Ensure we do not exceed MAX_DOCS (360)
    sample_size = min(len(dataset), MAX_DOCS)
    indices = random.sample(range(len(dataset)), sample_size)
    
    samples = []
    for idx in indices:
        item = dataset[idx]
        samples.append({
            "id": f"wiki_{idx}",
            "title": item.get('title', 'Unknown'),
            "text": item.get('text', ''),
            "source": "wikipedia"
        })
    
    return samples

def load_hotpotqa_query_set(split: str = "validation") -> List[Dict[str, Any]]:
    """
    Load the HotpotQA query set (validation split) to ensure strict disjointness
    from the training corpus (train split) used in load_hotpotqa_sample.
    
    This function prevents data leakage by sourcing queries from a different 
    dataset split than the training documents.
    
    Args:
        split: The dataset split to load (default: "validation"). 
               Options: "train" (for training), "validation" (for queries).
    
    Returns:
        A list of query dictionaries containing 'id', 'question', 'answer', 
        and 'type' (supporting facts).
    """
    # Use a different seed to ensure we sample different indices if we were 
    # to sample from the same set, but more importantly, we load a DIFFERENT split.
    random.seed(RANDOM_SEED + 100) 
    
    dataset = load_dataset("hotpot_qa", "fullwiki", split=split)
    
    # We limit the query set size as well to match the scale of the experiment
    sample_size = min(len(dataset), MAX_DOCS)
    indices = random.sample(range(len(dataset)), sample_size)
    
    queries = []
    for idx in indices:
        item = dataset[idx]
        queries.append({
            "id": f"hp_q_{idx}",
            "question": item.get('question', ''),
            "answer": item.get('answer', ''),
            "type": item.get('type', 'multi'),
            "source": "hotpot_qa"
        })
    
    return queries

def get_disjoint_corpus_and_queries() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Convenience function to retrieve the disjoint training corpus and query set.
    
    Returns:
        Tuple of (training_corpus, query_set)
        - training_corpus: Documents from HotpotQA train split (or Wikipedia)
        - query_set: Queries from HotpotQA validation split
    
    This ensures strict separation between the data used for building the 
    retrieval index and the data used for evaluating retrieval performance.
    """
    # Training corpus comes from the 'train' split
    training_corpus = load_hotpotqa_sample()
    
    # Query set comes from the 'validation' split
    query_set = load_hotpotqa_query_set(split="validation")
    
    # Verify disjointness by checking IDs (optional safety check)
    train_ids = {doc['id'] for doc in training_corpus}
    query_ids = {q['id'] for q in query_set}
    
    if train_ids & query_ids:
        raise RuntimeError("Data leakage detected: Training and Query sets share IDs.")
    
    return training_corpus, query_set