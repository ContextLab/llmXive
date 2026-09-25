"""
Schema validators for the data models.
Ensures data conforms to the contracts/ YAML schemas.
"""
import re
from typing import Any, Dict, List, Optional
from .document import Document, MiddleThirdMetadata, Page
from .evaluation import EvaluationResult, BaselineMetrics, RetrievalMetrics
from .stats import StatisticalResult

def validate_document_schema(data: Dict[str, Any]) -> None:
    """
    Validates a document dictionary against the expected schema.
    Raises ValueError if validation fails.
    """
    required_fields = ['document_id', 'title', 'total_pages', 'pdf_path', 'middle_third_metadata', 'pages']
    Document.validate_required_fields(data, required_fields, 'Document')

    # Validate document_id format (alphanumeric + underscore)
    if not re.match(r'^[a-zA-Z0-9_]+$', data['document_id']):
        raise ValueError(f"Invalid document_id format: {data['document_id']}")

    # Validate total_pages
    if not isinstance(data['total_pages'], int) or data['total_pages'] <= 0:
        raise ValueError(f"total_pages must be a positive integer, got {data['total_pages']}")

    # Validate middle_third_metadata
    mt_meta = data['middle_third_metadata']
    mt_required = ['start_page', 'end_page', 'total_pages', 'text_density', 'is_valid']
    MiddleThirdMetadata.validate_required_fields(mt_meta, mt_required, 'MiddleThirdMetadata')
    
    if not isinstance(mt_meta['is_valid'], bool):
        raise ValueError("is_valid must be a boolean")
    if not isinstance(mt_meta['text_density'], (int, float)) or not (0.0 <= mt_meta['text_density'] <= 1.0):
        raise ValueError(f"text_density must be between 0.0 and 1.0, got {mt_meta['text_density']}")

    # Validate pages
    if not isinstance(data['pages'], list) or len(data['pages']) != data['total_pages']:
        raise ValueError(f"pages list length ({len(data['pages'])}) must match total_pages ({data['total_pages']})")
    
    for i, page in enumerate(data['pages']):
        Page.validate_required_fields(page, ['page_number', 'image_path', 'text_content', 'text_density', 'is_middle_third'], 'Page')
        if page['page_number'] != i + 1:
            raise ValueError(f"Page numbers must be sequential starting from 1. Expected {i+1}, got {page['page_number']}")

def validate_evaluation_schema(data: Dict[str, Any], schema_type: str) -> None:
    """
    Validates evaluation data against the expected schema.
    schema_type: 'result', 'baseline', or 'retrieval'
    """
    if schema_type == 'result':
        required_fields = ['question_id', 'document_id', 'page_number', 'position_category', 
                         'ground_truth', 'predicted_answer', 'is_correct', 'model_id']
        EvaluationResult.validate_required_fields(data, required_fields, 'EvaluationResult')
        
        if data['position_category'] not in ['first', 'middle', 'last']:
            raise ValueError(f"Invalid position_category: {data['position_category']}")
        if not isinstance(data['is_correct'], bool):
            raise ValueError("is_correct must be a boolean")

    elif schema_type == 'baseline':
        required_fields = ['model_id', 'total_questions', 'correct_count', 'accuracy', 
                         'accuracy_by_position', 'delta_middle_vs_others', 'bias_threshold_met']
        BaselineMetrics.validate_required_fields(data, required_fields, 'BaselineMetrics')
        
        if not isinstance(data['accuracy_by_position'], dict):
            raise ValueError("accuracy_by_position must be a dictionary")
        for pos in ['first', 'middle', 'last']:
            if pos not in data['accuracy_by_position']:
                raise ValueError(f"Missing accuracy for position '{pos}' in accuracy_by_position")
        
        if not isinstance(data['bias_threshold_met'], bool):
            raise ValueError("bias_threshold_met must be a boolean")

    elif schema_type == 'retrieval':
        required_fields = ['model_id', 'total_questions', 'correct_count', 'accuracy', 
                         'precision', 'recall', 'false_positive_rate']
        RetrievalMetrics.validate_required_fields(data, required_fields, 'RetrievalMetrics')
        
        # Validate metric ranges
        for field in ['accuracy', 'precision', 'recall', 'false_positive_rate']:
            val = data[field]
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{field} must be between 0.0 and 1.0, got {val}")

def validate_stats_schema(data: Dict[str, Any]) -> None:
    """
    Validates statistical result data against the expected schema.
    """
    required_fields = ['model_id', 'baseline_accuracy', 'retrieval_accuracy', 'recovery_delta', 
                     'context_window_size', 'correlation_coefficient', 'p_value', 'classification']
    StatisticalResult.validate_required_fields(data, required_fields, 'StatisticalResult')

    if not isinstance(data['context_window_size'], int) or data['context_window_size'] <= 0:
        raise ValueError(f"context_window_size must be a positive integer, got {data['context_window_size']}")
    
    if data['classification'] not in ['inverse', 'no significant inverse relationship']:
        raise ValueError(f"Invalid classification: {data['classification']}")
    
    if not isinstance(data['easy_questions_degraded'], bool):
        raise ValueError("easy_questions_degraded must be a boolean")
