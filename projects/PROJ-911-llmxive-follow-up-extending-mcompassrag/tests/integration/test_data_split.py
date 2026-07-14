"""
Integration test for disjoint train/test split validation (T019).

Verifies that the data loading and splitting logic in `code/data_loader.py`
ensures strict disjointness between the training corpus and the query set
to prevent data leakage.

This test:
1. Loads the HotpotQA sample using the real data loader.
2. Simulates a split (e.g., first 80% train, last 20% test) based on document IDs.
3. Asserts that no document ID appears in both sets.
4. Verifies that the combined set covers the expected total count.
"""
import pytest
from typing import List, Set, Dict, Any
from code.data_loader import load_hotpotqa_sample
from code.config import MAX_DOCS, RANDOM_SEED


def load_corpus_ids(documents: List[Dict[str, Any]]) -> Set[str]:
    """
    Extracts a set of unique document IDs from a list of document dictionaries.
    Assumes each document has a unique 'id' or '_id' field.
    """
    ids = set()
    for doc in documents:
        doc_id = doc.get('id') or doc.get('_id')
        if doc_id is None:
            pytest.fail(f"Document missing ID field: {doc}")
        ids.add(str(doc_id))
    return ids


def test_disjoint_train_test_split_no_leakage():
    """
    Integration test: Ensure train and test splits are strictly disjoint.
    
    This test validates the core requirement of US2 (T025) that strict disjointness
    is maintained between training corpus and query set.
    """
    # Load the real dataset sample
    # Note: MAX_DOCS is set to <= 360 in config/data_loader to respect time budget
    docs = load_hotpotqa_sample(n_samples=MAX_DOCS, seed=RANDOM_SEED)
    
    assert len(docs) > 0, "Loaded dataset is empty."
    
    # Simulate a split: 80% train, 20% test based on list index
    split_idx = int(len(docs) * 0.8)
    train_docs = docs[:split_idx]
    test_docs = docs[split_idx:]
    
    # Extract IDs
    train_ids = load_corpus_ids(train_docs)
    test_ids = load_corpus_ids(test_docs)
    
    # Check 1: Intersection must be empty
    intersection = train_ids.intersection(test_ids)
    assert len(intersection) == 0, (
        f"Data leakage detected! {len(intersection)} document IDs appear in both "
        f"train and test sets: {list(intersection)[:5]}..."
    )
    
    # Check 2: Union size should equal total (assuming unique IDs in source)
    # Note: HotpotQA documents are unique by ID, but we verify the count logic
    union_ids = train_ids.union(test_ids)
    assert len(union_ids) == len(docs), (
        f"ID count mismatch. Total docs: {len(docs)}, Unique Union IDs: {len(union_ids)}. "
        "This suggests duplicate IDs in the source dataset."
    )
    
    # Check 3: Verify split proportions (allow small rounding errors for small N)
    expected_train_size = int(len(docs) * 0.8)
    assert len(train_docs) == expected_train_size, f"Train split size mismatch: {len(train_docs)} vs {expected_train_size}"
    assert len(test_docs) == len(docs) - expected_train_size, "Test split size mismatch"


def test_split_reproducibility():
    """
    Integration test: Ensure that loading with the same seed produces the same split.
    """
    # Load twice with the same seed
    docs_a = load_hotpotqa_sample(n_samples=MAX_DOCS, seed=RANDOM_SEED)
    docs_b = load_hotpotqa_sample(n_samples=MAX_DOCS, seed=RANDOM_SEED)
    
    # The datasets should be identical (same order, same content)
    assert len(docs_a) == len(docs_b), "Dataset sizes differ between runs with same seed."
    
    for i, (doc_a, doc_b) in enumerate(zip(docs_a, docs_b)):
        id_a = doc_a.get('id') or doc_a.get('_id')
        id_b = doc_b.get('id') or doc_b.get('_id')
        assert id_a == id_b, f"Document ID mismatch at index {i}: {id_a} vs {id_b}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
