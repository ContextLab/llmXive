"""
Tests for model definitions and training utilities.
"""
import pytest
import torch
import numpy as np
from pathlib import Path
import tempfile

from models.base import BaseModel, FrozenEmbeddingModel, ProjectionModel
from models.projection import MLPProjection, AttentionProjection, GatedProjection, create_projection_model
from models.trainer import Trainer, create_trainer

@pytest.fixture
def sample_embedding_dim():
    return 512

@pytest.fixture
def sample_tabular_dim():
    return 128

@pytest.fixture
def sample_output_dim():
    return 256

@pytest.fixture
def batch_size():
    return 4

class TestProjectionModels:
    """Tests for projection model architectures."""

    def test_mlp_projection_creation(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim):
        """Test MLPProjection can be instantiated."""
        model = MLPProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )
        assert model is not None
        assert isinstance(model, ProjectionModel)

    def test_mlp_projection_forward(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim, batch_size):
        """Test MLPProjection forward pass."""
        model = MLPProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )

        embeddings = torch.randn(batch_size, sample_embedding_dim)
        tabular = torch.randn(batch_size, sample_tabular_dim)

        with torch.no_grad():
            output = model.project(embeddings, tabular)

        assert output.shape == (batch_size, sample_output_dim)

    def test_attention_projection_creation(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim):
        """Test AttentionProjection can be instantiated."""
        model = AttentionProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )
        assert model is not None
        assert isinstance(model, ProjectionModel)

    def test_attention_projection_forward(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim, batch_size):
        """Test AttentionProjection forward pass."""
        model = AttentionProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )

        embeddings = torch.randn(batch_size, sample_embedding_dim)
        tabular = torch.randn(batch_size, sample_tabular_dim)

        with torch.no_grad():
            output = model.project(embeddings, tabular)

        assert output.shape == (batch_size, sample_output_dim)

    def test_gated_projection_creation(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim):
        """Test GatedProjection can be instantiated."""
        model = GatedProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )
        assert model is not None
        assert isinstance(model, ProjectionModel)

    def test_gated_projection_forward(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim, batch_size):
        """Test GatedProjection forward pass."""
        model = GatedProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )

        embeddings = torch.randn(batch_size, sample_embedding_dim)
        tabular = torch.randn(batch_size, sample_tabular_dim)

        with torch.no_grad():
            output = model.project(embeddings, tabular)

        assert output.shape == (batch_size, sample_output_dim)

    def test_create_projection_model_factory(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim):
        """Test factory function creates correct model types."""
        for model_type in ['mlp', 'attention', 'gated']:
            model = create_projection_model(
                model_type=model_type,
                embedding_dim=sample_embedding_dim,
                tabular_dim=sample_tabular_dim,
                output_dim=sample_output_dim
            )
            assert model is not None
            assert isinstance(model, ProjectionModel)

    def test_invalid_model_type(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim):
        """Test factory raises error for invalid model type."""
        with pytest.raises(ValueError):
            create_projection_model(
                model_type='invalid',
                embedding_dim=sample_embedding_dim,
                tabular_dim=sample_tabular_dim,
                output_dim=sample_output_dim
            )

class TestTrainer:
    """Tests for Trainer class."""

    def test_trainer_creation(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim):
        """Test Trainer can be instantiated."""
        model = MLPProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )
        trainer = create_trainer(model)
        assert trainer is not None
        assert isinstance(trainer, Trainer)

    def test_trainer_fit_creates_history(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim):
        """Test that training populates history."""
        model = MLPProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )
        trainer = create_trainer(model)

        # Create dummy data
        train_data = torch.utils.data.TensorDataset(
            torch.randn(8, sample_embedding_dim),
            torch.randn(8, sample_tabular_dim),
            torch.randn(8, sample_output_dim)
        )
        train_loader = torch.utils.data.DataLoader(train_data, batch_size=4)

        val_loader = torch.utils.data.DataLoader(train_data, batch_size=4)

        history = trainer.fit(train_loader, val_loader, epochs=2)

        assert 'train_loss' in history
        assert 'val_loss' in history
        assert len(history['train_loss']) == 2
        assert len(history['val_loss']) == 2

    def test_checkpoint_save_load(self, sample_embedding_dim, sample_tabular_dim, sample_output_dim):
        """Test checkpoint saving and loading."""
        model = MLPProjection(
            embedding_dim=sample_embedding_dim,
            tabular_dim=sample_tabular_dim,
            output_dim=sample_output_dim
        )
        trainer = create_trainer(model)

        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_path = Path(tmpdir) / "test_checkpoint.pt"
            trainer.save_checkpoint(checkpoint_path, epoch=1)

            assert checkpoint_path.exists()

            # Create new model and trainer
            model2 = MLPProjection(
                embedding_dim=sample_embedding_dim,
                tabular_dim=sample_tabular_dim,
                output_dim=sample_output_dim
            )
            trainer2 = create_trainer(model2)
            trainer2.load_checkpoint(checkpoint_path)

            # Check state dicts match
            for (name1, param1), (name2, param2) in zip(
                trainer.model.named_parameters(),
                trainer2.model.named_parameters()
            ):
                assert name1 == name2
                assert torch.equal(param1, param2)