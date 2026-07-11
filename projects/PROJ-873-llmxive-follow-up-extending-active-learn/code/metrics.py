import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.stats import wilcoxon
import os
import json
import logging
from dataclasses import dataclass, field

# Local imports based on API surface
from models import CandidateList, ComparisonPair
from data_loader import load_beir_corpus, load_trec_covid_corpus
from config import get_config

logger = logging.getLogger(__name__)

@dataclass
class StatisticalTestResult:
    """Result container for a single statistical test."""
    test_name: str
    statistic: float
    p_value: float
    significant_at_005: bool
    significant_at_01: bool
    description: str

@dataclass
class BonferroniResult:
    """Result container for Bonferroni-corrected hypothesis testing."""
    original_tests: List[StatisticalTestResult]
    corrected_results: List[StatisticalTestResult]
    alpha_threshold: float
    num_tests: int
    corrected_alpha: float
    summary: Dict[str, Any]

def get_embedding_model() -> SentenceTransformer:
    """Load the sentence transformer model for embeddings."""
    config = get_config()
    model_name = config.get('embedding_model', 'all-MiniLM-L6-v2')
    logger.info(f"Loading embedding model: {model_name}")
    return SentenceTransformer(model_name)

def calculate_cosine_similarity_proxy(doc1: str, doc2: str, model: SentenceTransformer) -> float:
    """Calculate cosine similarity between two document embeddings."""
    embeddings = model.encode([doc1, doc2], convert_to_numpy=True)
    sim = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(sim)

def is_wasted_call(similarity: float, threshold: float = 0.95) -> bool:
    """Determine if a call is 'wasted' based on similarity threshold."""
    return similarity > threshold

def calculate_ndcg_at_k(relevances: List[int], k: int) -> float:
    """Calculate NDCG@k for a list of relevance scores."""
    if not relevances or k <= 0:
        return 0.0
    
    dcg = 0.0
    idcg = 0.0
    
    # Calculate DCG
    for i, rel in enumerate(relevances[:k]):
        dcg += (2 ** rel - 1) / np.log2(i + 2)
    
    # Calculate IDCG
    sorted_relevances = sorted(relevances, reverse=True)
    for i, rel in enumerate(sorted_relevances[:k]):
        idcg += (2 ** rel - 1) / np.log2(i + 2)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg

def calculate_ndcg_at_10(relevances: List[int]) -> float:
    """Calculate NDCG@10 specifically."""
    return calculate_ndcg_at_k(relevances, 10)

def calculate_ndcg_from_beir_results(beir_results: Dict[str, Any], query_id: str, k: int = 10) -> float:
    """Extract NDCG@k from BEIR evaluation results."""
    if query_id not in beir_results:
        return 0.0
    return beir_results[query_id].get(f'ndcg@{k}', 0.0)

def load_beir_ground_truth(dataset_name: str) -> Dict[str, Any]:
    """Load ground truth relevance judgments for a BEIR dataset."""
    corpus = load_beir_corpus(dataset_name)
    # In a real implementation, this would load the qrels file
    # For now, we return the corpus structure which contains ground truth
    return corpus

def load_results_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Load experimental results from a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def aggregate_ndcg_scores(results: List[Dict[str, Any]], metric_key: str = 'ndcg@10') -> List[float]:
    """Aggregate NDCG scores across multiple queries/seeds."""
    scores = []
    for result in results:
        if metric_key in result:
            scores.append(result[metric_key])
    return scores

def wilcoxon_signed_rank_test(group1: List[float], group2: List[float]) -> StatisticalTestResult:
    """Perform Wilcoxon signed-rank test on two paired groups."""
    if len(group1) != len(group2):
        raise ValueError("Groups must be of equal length for paired test")
    
    statistic, p_value = wilcoxon(group1, group2)
    
    return StatisticalTestResult(
        test_name="Wilcoxon Signed-Rank",
        statistic=float(statistic),
        p_value=float(p_value),
        significant_at_005=p_value < 0.05,
        significant_at_01=p_value < 0.01,
        description="Paired non-parametric test comparing two related samples"
    )

def bonferroni_correction(test_results: List[StatisticalTestResult], alpha: float = 0.05) -> BonferroniResult:
    """
    Apply Bonferroni correction for multiple hypothesis testing.
    
    Args:
        test_results: List of StatisticalTestResult objects from individual tests
        alpha: Original significance level (default 0.05)
    
    Returns:
        BonferroniResult containing corrected results and summary
    """
    num_tests = len(test_results)
    if num_tests == 0:
        return BonferroniResult(
            original_tests=[],
            corrected_results=[],
            alpha_threshold=alpha,
            num_tests=0,
            corrected_alpha=1.0,
            summary={"message": "No tests to correct"}
        )
    
    # Calculate corrected alpha threshold
    corrected_alpha = alpha / num_tests
    
    corrected_results = []
    significant_count = 0
    significant_tests = []
    
    for test in test_results:
        # Apply Bonferroni correction: reject if p-value < alpha/n
        is_significant = test.p_value < corrected_alpha
        
        corrected_test = StatisticalTestResult(
            test_name=test.test_name,
            statistic=test.statistic,
            p_value=test.p_value,
            significant_at_005=is_significant,  # Now using corrected threshold
            significant_at_01=is_significant and test.p_value < (corrected_alpha / 10),
            description=f"{test.description} (Bonferroni-corrected, n={num_tests})"
        )
        
        corrected_results.append(corrected_test)
        
        if is_significant:
            significant_count += 1
            significant_tests.append(test.test_name)
    
    summary = {
        "num_tests": num_tests,
        "original_alpha": alpha,
        "corrected_alpha": corrected_alpha,
        "significant_tests_count": significant_count,
        "significant_tests": significant_tests,
        "correction_method": "Bonferroni"
    }
    
    logger.info(f"Bonferroni correction applied: {num_tests} tests, corrected alpha = {corrected_alpha:.6f}")
    logger.info(f"Significant results after correction: {significant_count}/{num_tests}")
    
    return BonferroniResult(
        original_tests=test_results,
        corrected_results=corrected_results,
        alpha_threshold=alpha,
        num_tests=num_tests,
        corrected_alpha=corrected_alpha,
        summary=summary
    )

def calculate_ndcg_for_clustering_aided_variant(relevances: List[int], k: int = 10) -> float:
    """Calculate NDCG@k for clustering-aided variant results."""
    return calculate_ndcg_at_k(relevances, k)

def validate_proxy_accuracy(flagged_calls: List[Dict[str, Any]], llm_labels: List[bool]) -> float:
    """Validate the cosine similarity proxy against LLM ground truth."""
    if len(flagged_calls) != len(llm_labels):
        raise ValueError("Flagged calls and LLM labels must have same length")
    
    correct = sum(1 for call, label in zip(flagged_calls, llm_labels) 
                 if call.get('is_wasted') == label)
    
    return correct / len(llm_labels) if llm_labels else 0.0

def calculate_dynamic_sample_size(total_flagged: int, upper_bound: int = 100) -> int:
    """Calculate dynamic sample size for LLM validation."""
    return min(total_flagged, upper_bound)

def validate_jaccard_cosine_correlation(jaccard_scores: List[float], cosine_scores: List[float]) -> float:
    """Validate correlation between Jaccard (MinHash) and Cosine similarity."""
    if len(jaccard_scores) != len(cosine_scores):
        raise ValueError("Score lists must be equal length")
    
    if len(jaccard_scores) < 2:
        return 0.0
    
    correlation = np.corrcoef(jaccard_scores, cosine_scores)[0, 1]
    return float(correlation)

def main():
    """Main entry point for metrics module testing."""
    logger.info("Metrics module loaded successfully")
    
    # Example usage of Bonferroni correction
    test_results = [
        StatisticalTestResult("NDCG Comparison", 12.5, 0.003, True, True, "NDCG improvement test"),
        StatisticalTestResult("Efficiency Ratio", 8.2, 0.012, False, False, "Wasted call ratio test"),
        StatisticalTestResult("Runtime Overhead", 3.1, 0.045, True, False, "Runtime penalty test")
    ]
    
    bonf_result = bonferroni_correction(test_results, alpha=0.05)
    
    print(f"Original tests: {bonf_result.num_tests}")
    print(f"Corrected alpha: {bonf_result.corrected_alpha:.6f}")
    print(f"Significant after correction: {bonf_result.summary['significant_tests_count']}")
    print(f"Significant tests: {bonf_result.summary['significant_tests']}")

if __name__ == "__main__":
    main()