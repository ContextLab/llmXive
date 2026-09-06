"""
Unit tests for data models and schema validators.
"""
import pytest
from code.models.document import Document, Page, MiddleThirdMetadata
from code.models.evaluation import EvaluationResult, BaselineMetrics, RetrievalMetrics
from code.models.stats import StatisticalResult

class TestMiddleThirdMetadata:
    def test_valid_creation(self):
        meta = MiddleThirdMetadata(
            start_page=10,
            end_page=20,
            text_density=0.75,
            character_count=5000
        )
        assert meta.start_page == 10
        assert meta.end_page == 20
        assert meta.text_density == 0.75
        assert meta.character_count == 5000

    def test_missing_required_field(self):
        with pytest.raises(ValueError, match="Missing required field"):
            MiddleThirdMetadata(
                start_page=10,
                end_page=20,
                text_density=0.75
                # missing character_count
            )

    def test_wrong_type(self):
        with pytest.raises(ValueError, match="must be integer"):
            MiddleThirdMetadata(
                start_page=10.5,  # should be int
                end_page=20,
                text_density=0.75,
                character_count=5000
            )

class TestPage:
    def test_valid_creation(self):
        page = Page(
            page_id="p1",
            page_number=1,
            text_density=0.6,
            character_count=1000
        )
        assert page.page_id == "p1"
        assert page.page_number == 1
        assert page.text_density == 0.6

    def test_with_layout_info(self):
        page = Page(
            page_id="p2",
            page_number=2,
            text_density=0.8,
            character_count=2000,
            layout_info={"columns": 2}
        )
        assert page.layout_info == {"columns": 2}

class TestDocument:
    def test_valid_creation(self):
        middle_third = MiddleThirdMetadata(10, 20, 0.75, 5000)
        pages = [
            Page("p1", 1, 0.5, 500),
            Page("p2", 2, 0.6, 600)
        ]
        doc = Document(
            doc_id="doc1",
            title="Test Document",
            total_pages=2,
            pdf_path="data/raw/test.pdf",
            middle_third=middle_third,
            pages=pages
        )
        assert doc.doc_id == "doc1"
        assert doc.title == "Test Document"
        assert len(doc.pages) == 2

    def test_from_dict(self):
        data = {
            "doc_id": "doc1",
            "title": "Test",
            "total_pages": 2,
            "pdf_path": "data/raw/test.pdf",
            "middle_third": {
                "start_page": 10,
                "end_page": 20,
                "text_density": 0.75,
                "character_count": 5000
            },
            "pages": [
                {"page_id": "p1", "page_number": 1, "text_density": 0.5, "character_count": 500},
                {"page_id": "p2", "page_number": 2, "text_density": 0.6, "character_count": 600}
            ]
        }
        doc = Document.from_dict(data)
        assert doc.doc_id == "doc1"
        assert doc.middle_third.start_page == 10

class TestEvaluationResult:
    def test_valid_creation(self):
        result = EvaluationResult(
            question_id="q1",
            doc_id="doc1",
            position="middle",
            model_name="model-a",
            answer="The answer is 42.",
            is_correct=True
        )
        assert result.is_correct is True
        assert result.position == "middle"

class TestBaselineMetrics:
    def test_valid_creation(self):
        metrics = BaselineMetrics(
            model_name="model-a",
            overall_accuracy=0.75,
            first_third_accuracy=0.85,
            middle_third_accuracy=0.60,
            last_third_accuracy=0.80,
            delta_middle_vs_others=-0.175,
            bias_threshold_met=False,
            total_questions=100,
            correct_count=75
        )
        assert metrics.bias_threshold_met is False
        assert metrics.delta_middle_vs_others == -0.175

class TestRetrievalMetrics:
    def test_valid_creation(self):
        metrics = RetrievalMetrics(
            model_name="model-a",
            overall_accuracy=0.80,
            middle_third_accuracy=0.75,
            retrieval_precision=0.90,
            retrieval_recall=0.85,
            false_positive_rate=0.05,
            avg_tokens_used=1500.0,
            total_questions=100
        )
        assert metrics.false_positive_rate == 0.05

class TestStatisticalResult:
    def test_valid_creation(self):
        result = StatisticalResult(
            spearman_r=-0.65,
            p_value=0.02,
            classification="inverse",
            recovery_deltas=[0.15, 0.10, 0.05],
            context_sizes=[8000, 16000, 32000],
            models=["model-a", "model-b", "model-c"]
        )
        assert result.classification == "inverse"
        assert result.spearman_r == -0.65

    def test_no_significant_classification(self):
        result = StatisticalResult(
            spearman_r=-0.20,
            p_value=0.15,
            classification="no significant inverse relationship",
            recovery_deltas=[0.05],
            context_sizes=[8000],
            models=["model-a"]
        )
        assert result.classification == "no significant inverse relationship"
