"""
Unit tests for data models and schema validators.
"""
import pytest
import json
from code.models.document import Document, MiddleThirdMetadata, Page
from code.models.evaluation import EvaluationResult, BaselineMetrics, RetrievalMetrics
from code.models.stats import StatisticalResult
from code.models.validators import (
    validate_document_schema,
    validate_evaluation_schema,
    validate_stats_schema
)

class TestDocumentModels:
    def test_middle_third_metadata_creation(self):
        meta = MiddleThirdMetadata(
            start_page=10,
            end_page=20,
            total_pages=30,
            text_density=0.85,
            is_valid=True
        )
        assert meta.start_page == 10
        assert meta.text_density == 0.85
        assert meta.is_valid is True

    def test_page_creation(self):
        page = Page(
            page_number=1,
            image_path="data/raw/doc_001/page_001.png",
            text_content="Sample text",
            text_density=0.6,
            is_middle_third=False
        )
        assert page.page_number == 1
        assert page.is_middle_third is False

    def test_document_creation(self):
        meta = MiddleThirdMetadata(10, 20, 30, 0.85, True)
        pages = [
            Page(i, f"path_{i}", f"text_{i}", 0.5, 10 <= i <= 20)
            for i in range(1, 31)
        ]
        doc = Document(
            document_id="doc_001",
            title="Test Document",
            total_pages=30,
            pdf_path="data/raw/doc_001.pdf",
            middle_third_metadata=meta,
            pages=pages
        )
        
        assert doc.document_id == "doc_001"
        assert len(doc.pages) == 30
        assert doc.middle_third_metadata.is_valid is True

    def test_document_serialization(self):
        meta = MiddleThirdMetadata(10, 20, 30, 0.85, True)
        pages = [Page(i, f"path_{i}", f"text_{i}", 0.5, False) for i in range(1, 4)]
        doc = Document(
            document_id="doc_001",
            title="Test",
            total_pages=3,
            pdf_path="test.pdf",
            middle_third_metadata=meta,
            pages=pages
        )
        
        json_str = doc.to_json()
        restored = Document.from_json(json_str)
        
        assert restored.document_id == doc.document_id
        assert restored.total_pages == doc.total_pages

    def test_document_validation_success(self):
        data = {
            "document_id": "valid_doc_123",
            "title": "Valid Doc",
            "total_pages": 2,
            "pdf_path": "test.pdf",
            "middle_third_metadata": {
                "start_page": 1,
                "end_page": 2,
                "total_pages": 2,
                "text_density": 0.5,
                "is_valid": True
            },
            "pages": [
                {"page_number": 1, "image_path": "p1.png", "text_content": "t1", "text_density": 0.5, "is_middle_third": False},
                {"page_number": 2, "image_path": "p2.png", "text_content": "t2", "text_density": 0.5, "is_middle_third": False}
            ]
        }
        # Should not raise
        validate_document_schema(data)

    def test_document_validation_invalid_id(self):
        data = {
            "document_id": "invalid@id",
            "title": "Test",
            "total_pages": 1,
            "pdf_path": "test.pdf",
            "middle_third_metadata": {
                "start_page": 1, "end_page": 1, "total_pages": 1, "text_density": 0.5, "is_valid": True
            },
            "pages": [
                {"page_number": 1, "image_path": "p.png", "text_content": "t", "text_density": 0.5, "is_middle_third": False}
            ]
        }
        with pytest.raises(ValueError, match="Invalid document_id format"):
            validate_document_schema(data)

    def test_document_validation_page_count_mismatch(self):
        data = {
            "document_id": "doc_1",
            "title": "Test",
            "total_pages": 2,
            "pdf_path": "test.pdf",
            "middle_third_metadata": {
                "start_page": 1, "end_page": 2, "total_pages": 2, "text_density": 0.5, "is_valid": True
            },
            "pages": [
                {"page_number": 1, "image_path": "p1.png", "text_content": "t1", "text_density": 0.5, "is_middle_third": False}
                # Missing second page
            ]
        }
        with pytest.raises(ValueError, match="pages list length"):
            validate_document_schema(data)

class TestEvaluationModels:
    def test_evaluation_result_creation(self):
        result = EvaluationResult(
            question_id="q_001",
            document_id="doc_001",
            page_number=5,
            position_category="middle",
            ground_truth="Answer A",
            predicted_answer="Answer A",
            is_correct=True,
            model_id="model_v1"
        )
        assert result.is_correct is True
        assert result.position_category == "middle"

    def test_baseline_metrics_creation(self):
        metrics = BaselineMetrics(
            model_id="model_v1",
            total_questions=100,
            correct_count=85,
            accuracy=0.85,
            accuracy_by_position={"first": 0.9, "middle": 0.7, "last": 0.9},
            delta_middle_vs_others=0.15,
            bias_threshold_met=True
        )
        assert metrics.delta_middle_vs_others == 0.15
        assert metrics.bias_threshold_met is True

    def test_retrieval_metrics_creation(self):
        metrics = RetrievalMetrics(
            model_id="model_v1",
            total_questions=100,
            correct_count=90,
            accuracy=0.90,
            precision=0.85,
            recall=0.92,
            false_positive_rate=0.05
        )
        assert metrics.precision == 0.85
        assert metrics.false_positive_rate == 0.05

    def test_evaluation_validation_success(self):
        data = {
            "question_id": "q_001",
            "document_id": "doc_001",
            "page_number": 1,
            "position_category": "first",
            "ground_truth": "A",
            "predicted_answer": "A",
            "is_correct": True,
            "model_id": "m1"
        }
        validate_evaluation_schema(data, "result")

    def test_evaluation_validation_invalid_position(self):
        data = {
            "question_id": "q_001",
            "document_id": "doc_001",
            "page_number": 1,
            "position_category": "invalid",
            "ground_truth": "A",
            "predicted_answer": "A",
            "is_correct": True,
            "model_id": "m1"
        }
        with pytest.raises(ValueError, match="Invalid position_category"):
            validate_evaluation_schema(data, "result")

class TestStatsModels:
    def test_statistical_result_creation(self):
        result = StatisticalResult(
            model_id="m1",
            baseline_accuracy=0.7,
            retrieval_accuracy=0.85,
            recovery_delta=0.15,
            context_window_size=8192,
            correlation_coefficient=-0.45,
            p_value=0.02,
            classification="inverse",
            easy_questions_degraded=False
        )
        assert result.correlation_coefficient == -0.45
        assert result.classification == "inverse"

    def test_stats_validation_success(self):
        data = {
            "model_id": "m1",
            "baseline_accuracy": 0.7,
            "retrieval_accuracy": 0.85,
            "recovery_delta": 0.15,
            "context_window_size": 8192,
            "correlation_coefficient": -0.45,
            "p_value": 0.02,
            "classification": "inverse",
            "easy_questions_degraded": False
        }
        validate_stats_schema(data)

    def test_stats_validation_invalid_classification(self):
        data = {
            "model_id": "m1",
            "baseline_accuracy": 0.7,
            "retrieval_accuracy": 0.85,
            "recovery_delta": 0.15,
            "context_window_size": 8192,
            "correlation_coefficient": -0.45,
            "p_value": 0.02,
            "classification": "invalid_class",
            "easy_questions_degraded": False
        }
        with pytest.raises(ValueError, match="Invalid classification"):
            validate_stats_schema(data)