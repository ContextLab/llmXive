import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

# Ensure NLTK data is available
try:
    stopwords_set = set(stopwords.words('english'))
except:
    stopwords_set = set(['the', 'is', 'at', 'which', 'on'])

class TfidfIndex:
    def __init__(self, vocabulary: Dict[str, int], idf: Dict[str, float], documents: Dict[str, List[str]]):
        self.vocabulary = vocabulary
        self.idf = idf
        self.documents = documents

def stream_file_lines(file_path: Path, chunk_size: int = 1024) -> str:
    """Read file content in chunks to handle large files."""
    content = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                content.append(chunk)
    except Exception:
        return ""
    return "".join(content)

def chunk_file_content(content: str, max_tokens: int = 500) -> List[str]:
    """Split content into chunks roughly by token count (approx)."""
    # Simple split by lines for now, assuming avg 4 chars per token
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_len = 0
    
    for line in lines:
        if current_len + len(line) > max_tokens * 4:
            chunks.append('\n'.join(current_chunk))
            current_chunk = []
            current_len = 0
        current_chunk.append(line)
        current_len += len(line)
    
    if current_chunk:
        chunks.append('\n'.join(current_chunk))
    return chunks

def build_tfidf_index(files: Dict[str, str]) -> TfidfIndex:
    """
    Build a TF-IDF index from a dictionary of file paths to content.
    Handles large repos by streaming and chunking.
    """
    # Preprocess: clean content and tokenize
    documents = []
    doc_ids = []
    
    for path, content in files.items():
        # Simple tokenization: split by non-word chars
        tokens = re.findall(r'\w+', content.lower())
        # Filter stopwords
        tokens = [t for t in tokens if t not in stopwords_set and len(t) > 2]
        if tokens:
            documents.append(" ".join(tokens))
            doc_ids.append(path)
    
    if not documents:
        return TfidfIndex({}, {}, {})
    
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=10000,
        analyzer='word',
        stop_words=None # Already filtered
    )
    
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    vocabulary = vectorizer.get_feature_names_out()
    vocabulary_map = {word: i for i, word in enumerate(vocabulary)}
    
    idf = vectorizer.id_
    idf_map = {vocabulary[i]: float(idf[i]) for i in range(len(idf))}
    
    # Store document contents for retrieval
    doc_contents = {path: content for path, content in files.items()}
    
    return TfidfIndex(vocabulary_map, idf_map, doc_contents)

def search_tfidf(index: TfidfIndex, query: List[str]) -> Dict[str, float]:
    """Search the index for a list of keywords."""
    if not index.vocabulary:
        return {}
    
    # Convert query to TF-IDF vector
    query_text = " ".join(query)
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=10000,
        analyzer='word',
        stop_words=None
    )
    
    # Fit on query only to get vector, but we need to map to existing vocab
    # Simpler approach: calculate cosine similarity manually with existing IDFs
    query_tokens = re.findall(r'\w+', query_text.lower())
    query_tokens = [t for t in query_tokens if t in index.vocabulary and len(t) > 2]
    
    if not query_tokens:
        return {}
    
    # Calculate scores for each document
    scores = {}
    for path, content in index.documents.items():
        doc_tokens = re.findall(r'\w+', content.lower())
        doc_tokens = [t for t in doc_tokens if t in index.vocabulary]
        
        if not doc_tokens:
            continue
          
        # Simple dot product approximation
        score = 0.0
        for t in query_tokens:
            if t in doc_tokens:
                score += index.idf.get(t, 0.0)
        
        if score > 0:
            scores[path] = score
    
    return scores

def extract_snippets(repo_files: Dict[str, str], keywords: List[str], top_k: int = 5) -> List[str]:
    """Extract top-K snippets based on keyword matching."""
    if not repo_files:
        return []
    
    index = build_tfidf_index(repo_files)
    scores = search_tfidf(index, keywords)
    
    sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    snippets = []
    for path, score in sorted_files[:top_k]:
        # Return a snippet (first 200 chars of the file)
        content = repo_files.get(path, "")
        snippet = content[:200] + "..." if len(content) > 200 else content
        snippets.append(f"[{path}]\n{snippet}")
    
    return snippets

def filter_files_by_target_dirs(files: Dict[str, str], target_dirs: List[str]) -> Dict[str, str]:
    """Filter files to only those in target directories."""
    filtered = {}
    for path, content in files.items():
        for d in target_dirs:
            if path.startswith(d) or path.startswith(f"./{d}"):
                filtered[path] = content
                break
    return filtered

def run_fastcontext_lite(repo_files: Dict[str, str], issue_text: str) -> Dict:
    """Run the full FastContext-Lite pipeline."""
    start_time = time.time()
    
    # Extract keywords
    keywords = extract_keywords(issue_text)
    
    # Filter files
    filtered_files = filter_files_by_target_dirs(repo_files, ['src/', 'tests/', 'docs/', 'src', 'tests', 'docs'])
    
    # Extract snippets
    snippets = extract_snippets(filtered_files, keywords, top_k=5)
    
    latency = time.time() - start_time
    tokens = sum(len(s.split()) for s in snippets)
    
    return {
        'retrieved_snippets': snippets,
        'token_count': tokens,
        'latency_ms': round(latency * 1000, 2)
    }

def extract_keywords(issue_text: str) -> List[str]:
    """Extract keywords from issue text using TF-IDF logic (simplified for pilot)."""
    # Simple extraction: split by non-word chars and filter stopwords
    tokens = re.findall(r'\w+', issue_text.lower())
    keywords = [t for t in tokens if t not in stopwords_set and len(t) > 2]
    return keywords[:10] # Limit to top 10

def main():
    # Demo run
    mock_repo = {
        'src/main.py': 'def main():\n    print("Hello")\n',
        'tests/test_main.py': 'def test_main():\n    assert True\n'
    }
    issue = "Fix the main function to print hello"
    
    result = run_fastcontext_lite(mock_repo, issue)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
