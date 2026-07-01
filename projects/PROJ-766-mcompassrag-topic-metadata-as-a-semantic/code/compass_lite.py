import os
import json
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from datasets import load_dataset

# --- Configuration ---
SEED = 42
NUM_CHUNKS = 100  # Small sample for CPU tractability
NUM_QUERIES = 20
TOPIC_K = 5       # Number of topics
LAMBDA_COMPASS = 0.3  # Weight for topic signal

random.seed(SEED)
np.random.seed(SEED)

def load_and_chunk_data():
    """
    Loads 20newsgroups (a real dataset) and creates simple chunks.
    Simulates the 'heterogeneous corpus' with distinct topics.
    """
    print("Loading real data (20newsgroups)...")
    # Load a subset to keep it fast
    ds = load_dataset("20newsgroups", split="train", streaming=True)
    
    chunks = []
    count = 0
    for item in ds:
        if count >= NUM_CHUNKS:
            break
        # Simple chunk: the whole text (since it's short enough for this demo)
        # In the real paper, chunks are smaller paragraphs.
        text = item["text"]
        if len(text.strip()) < 50:
            continue
        chunks.append({
            "id": f"chunk_{count}",
            "text": text,
            "topic_label": item["target"] # Ground truth for evaluation
        })
        count += 1
    
    # If we didn't get enough, pad with duplicates (not ideal, but safe for demo)
    while len(chunks) < NUM_CHUNKS:
        chunks.append(chunks[-1])
        
    return chunks[:NUM_CHUNKS]

def build_topic_model(chunks):
    """
    Builds a lightweight LDA topic model on the chunks.
    Returns:
        - chunk_topic_matrix: (N_chunks, K)
        - vectorizer: TF-IDF for text
        - topic_vectorizer: TF for topic assignment
    """
    print("Building Topic Model (LDA on TF-IDF)...")
    texts = [c["text"] for c in chunks]
    
    # TF-IDF for LDA
    tfidf = TfidfVectorizer(max_features=1000, stop_words="english")
    tfidf_matrix = tfidf.fit_transform(texts)
    
    # LDA
    lda = LatentDirichletAllocation(n_components=TOPIC_K, random_state=SEED)
    chunk_topic_matrix = lda.fit_transform(tfidf_matrix)
    
    # Normalize to probability distributions
    chunk_topic_matrix = chunk_topic_matrix / (chunk_topic_matrix.sum(axis=1, keepdims=True) + 1e-9)
    
    return chunk_topic_matrix, tfidf

def generate_queries_and_ground_truth(chunks, encoder):
    """
    Generates synthetic queries based on real chunks to ensure a 'Hit' exists.
    This is a standard evaluation protocol: Query = Perturbed Chunk.
    """
    print("Generating Queries and Ground Truth...")
    queries = []
    ground_truth = []
    
    # Select random chunks to be the "target" for queries
    target_indices = random.sample(range(len(chunks)), NUM_QUERIES)
    
    for i, idx in enumerate(target_indices):
        target_chunk = chunks[idx]
        
        # Create a query by taking the first sentence or a subset of the text
        # This simulates a user asking about the content of this chunk
        text = target_chunk["text"]
        sentences = text.split(".")
        query_text = sentences[0].strip() if sentences else text[:100]
        if not query_text:
            query_text = text[:100]
            
        # Add a bit of noise or variation to make it non-trivial
        # (In a real setup, this would be an LLM-generated query)
        query_text = query_text + " " + "summary"
        
        queries.append({
            "id": f"query_{i}",
            "text": query_text,
            "target_id": target_chunk["id"],
            "target_label": target_chunk["topic_label"]
        })
        ground_truth.append(target_chunk["id"])
        
    return queries, ground_truth

def compute_embeddings(chunks, queries, encoder):
    """
    Computes dense embeddings for chunks and queries using Sentence-BERT.
    """
    print("Computing Dense Embeddings (Sentence-BERT)...")
    chunk_texts = [c["text"] for c in chunks]
    query_texts = [q["text"] for q in queries]
    
    # Batch processing
    chunk_embs = encoder.encode(chunk_texts, show_progress_bar=False)
    query_embs = encoder.encode(query_texts, show_progress_bar=False)
    
    return chunk_embs, query_embs

def retrieve_baseline(query_emb, chunk_embs, k=5):
    """
    Standard Dense Retrieval: Cosine Similarity.
    """
    sims = cosine_similarity([query_emb], chunk_embs)[0]
    top_k_indices = np.argsort(sims)[::-1][:k]
    return top_k_indices, sims[top_k_indices]

def retrieve_compass(query_emb, chunk_embs, chunk_topic_matrix, query_texts, chunk_texts, k=5):
    """
    MCompassRAG Adaptation:
    1. Baseline retrieval to get a 'context' of relevant topics.
    2. Construct a 'Topic Query' by averaging the topic distributions of the top-K baseline results.
    3. Score = Cosine(Query, Chunk) + Lambda * Cosine(Topic_Query, Chunk_Topics).
    """
    # Step 1: Baseline to get context
    baseline_indices, _ = retrieve_baseline(query_emb, chunk_embs, k=min(k, 10))
    
    # Step 2: Construct Topic Query
    # Average the topic distributions of the top baseline results
    context_topics = chunk_topic_matrix[baseline_indices].mean(axis=0)
    
    # Step 3: Compute Compass Score
    # We need to map the 'Topic Query' back to the embedding space?
    # The paper uses a shared space. Here, we simulate the 'Topic Embedding' 
    # by projecting the topic distribution back via a simple linear layer or 
    # by using the topic distribution directly in the scoring if dimensions match.
    # 
    # Simplified Approach for CPU:
    # Since we don't have the trained 'Compass Retriever' weights, we approximate
    # the 'Topic Signal' as a direct boost based on topic similarity.
    # We assume the 'Topic Embedding' is the topic vector itself (normalized).
    
    # Normalize topic vectors
    chunk_topics_norm = chunk_topic_matrix / (np.linalg.norm(chunk_topic_matrix, axis=1, keepdims=True) + 1e-9)
    context_topics_norm = context_topics / (np.linalg.norm(context_topics) + 1e-9)
    
    # Compute topic similarity
    topic_sims = cosine_similarity([context_topics_norm], chunk_topics_norm)[0]
    
    # Compute text similarity
    text_sims = cosine_similarity([query_emb], chunk_embs)[0]
    
    # Final Score
    final_scores = text_sims + LAMBDA_COMPASS * topic_sims
    
    top_k_indices = np.argsort(final_scores)[::-1][:k]
    return top_k_indices, final_scores[top_k_indices]

def evaluate(queries, ground_truth, chunk_ids, baseline_indices_list, compass_indices_list):
    """
    Calculates Hit Rate@K and MRR.
    """
    hits_baseline = 0
    mrr_baseline = 0.0
    
    hits_compass = 0
    mrr_compass = 0.0
    
    results = []
    
    for i, (query, target_id, b_indices, c_indices) in enumerate(zip(queries, ground_truth, baseline_indices_list, compass_indices_list)):
        # Baseline
        b_rank = None
        for rank, idx in enumerate(b_indices):
            if chunk_ids[idx] == target_id:
                b_rank = rank + 1
                break
        
        if b_rank:
            hits_baseline += 1
            mrr_baseline += 1.0 / b_rank
        
        # Compass
        c_rank = None
        for rank, idx in enumerate(c_indices):
            if chunk_ids[idx] == target_id:
                c_rank = rank + 1
                break
        
        if c_rank:
            hits_compass += 1
            mrr_compass += 1.0 / c_rank
            
        results.append({
            "query_id": query["id"],
            "target_id": target_id,
            "baseline_rank": b_rank if b_rank else -1,
            "compass_rank": c_rank if c_rank else -1,
            "baseline_hit": 1 if b_rank else 0,
            "compass_hit": 1 if c_rank else 0
        })
        
    n = len(queries)
    hr_b = hits_baseline / n
    mrr_b = mrr_baseline / n
    hr_c = hits_compass / n
    mrr_c = mrr_compass / n
    
    return results, {
        "baseline": {"HR@5": hr_b, "MRR": mrr_b},
        "compass": {"HR@5": hr_c, "MRR": mrr_c}
    }

def main():
    # Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("figures", exist_ok=True)
    
    # 1. Load Data
    chunks = load_and_chunk_data()
    chunk_ids = [c["id"] for c in chunks]
    
    # 2. Build Topic Model
    chunk_topic_matrix, tfidf = build_topic_model(chunks)
    
    # 3. Load Encoder (CPU safe)
    print("Loading Sentence-BERT (CPU)...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 4. Generate Queries
    queries, ground_truth = generate_queries_and_ground_truth(chunks, encoder)
    
    # 5. Compute Embeddings
    chunk_embs, query_embs = compute_embeddings(chunks, queries, encoder)
    
    # 6. Run Retrieval
    print("Running Baseline Retrieval...")
    baseline_results = [retrieve_baseline(q_emb, chunk_embs, k=5) for q_emb in query_embs]
    
    print("Running Compass Retrieval...")
    compass_results = [
        retrieve_compass(q_emb, chunk_embs, chunk_topic_matrix, [q["text"] for q in queries], chunk_ids, k=5)
        for q_emb in query_embs
    ]
    
    # 7. Evaluate
    detailed_results, metrics = evaluate(
        queries, ground_truth, chunk_ids,
        [r[0] for r in baseline_results],
        [r[0] for r in compass_results]
    )
    
    # 8. Save Outputs
    df = pd.DataFrame(detailed_results)
    df.to_csv("data/results.csv", index=False)
    
    # Save summary metrics
    with open("data/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
        
    print("\n--- Results Summary ---")
    print(f"Baseline HR@5: {metrics['baseline']['HR@5']:.4f}")
    print(f"Compass HR@5:  {metrics['compass']['HR@5']:.4f}")
    print(f"Improvement:   {(metrics['compass']['HR@5'] - metrics['baseline']['HR@5'])*100:.2f}%")
    
    # 9. Plot
    plt.figure(figsize=(8, 5))
    methods = ["Baseline", "Compass"]
    hr_scores = [metrics["baseline"]["HR@5"], metrics["compass"]["HR@5"]]
    mrr_scores = [metrics["baseline"]["MRR"], metrics["compass"]["MRR"]]
    
    x = np.arange(len(methods))
    width = 0.35
    
    plt.bar(x - width/2, hr_scores, width, label='Hit Rate@5', color=['#6b8ec2', '#e377c2'])
    plt.bar(x + width/2, mrr_scores, width, label='MRR', color=['#9ecae1', '#f7b6d2'])
    
    plt.xticks(x, methods)
    plt.ylabel('Score')
    plt.title('MCompassRAG Adaptation: Retrieval Performance')
    plt.legend()
    plt.ylim(0, 1.1)
    plt.tight_layout()
    plt.savefig("figures/comparison.png", dpi=150)
    plt.close()
    
    print("\nArtifacts saved to data/ and figures/")

if __name__ == "__main__":
    main()
