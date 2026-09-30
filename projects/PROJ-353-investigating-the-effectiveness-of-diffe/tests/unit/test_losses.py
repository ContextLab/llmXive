import torch
import pytest
import sys
import os

# Add parent directory to path for imports if running from tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from losses import cross_entropy_loss, info_nce_loss, LinearProbe, compute_accuracy

@pytest.fixture
def dummy_data():
    batch_size = 32
    num_classes = 10
    embedding_dim = 64
    device = torch.device("cpu")
    
    logits = torch.randn(batch_size, num_classes, device=device)
    targets = torch.randint(0, num_classes, (batch_size,), device=device)
    query = torch.randn(batch_size, embedding_dim, device=device)
    key = torch.randn(batch_size, embedding_dim, device=device)
    
    return {
        "logits": logits,
        "targets": targets,
        "query": query,
        "key": key,
        "num_classes": num_classes,
        "embedding_dim": embedding_dim
    }

def test_cross_entropy_loss_basic(dummy_data):
    """Test that CE loss returns a positive scalar."""
    loss = cross_entropy_loss(dummy_data["logits"], dummy_data["targets"])
    assert loss.dim() == 0
    assert loss.item() >= 0.0

def test_cross_entropy_loss_perfect(dummy_data):
    """Test that CE loss is near zero for perfect predictions."""
    # Create logits that guarantee correct prediction
    perfect_logits = torch.zeros_like(dummy_data["logits"])
    perfect_logits[torch.arange(32), dummy_data["targets"]] = 1e6
    
    loss = cross_entropy_loss(perfect_logits, dummy_data["targets"])
    assert loss.item() < 1e-4

def test_info_nce_loss_basic(dummy_data):
    """Test that InfoNCE loss returns a positive scalar."""
    loss = info_nce_loss(dummy_data["query"], dummy_data["key"])
    assert loss.dim() == 0
    assert loss.item() >= 0.0

def test_info_nce_loss_temperature(dummy_data):
    """Test that InfoNCE loss changes with temperature."""
    loss_low = info_nce_loss(dummy_data["query"], dummy_data["key"], temperature=0.01)
    loss_high = info_nce_loss(dummy_data["query"], dummy_data["key"], temperature=1.0)
    # Losses should be different
    assert not torch.isclose(loss_low, loss_high, atol=1e-5)

def test_linear_probe_forward(dummy_data):
    """Test LinearProbe forward pass shape."""
    probe = LinearProbe(dummy_data["embedding_dim"], dummy_data["num_classes"])
    out = probe(dummy_data["query"])
    assert out.shape == (dummy_data["query"].shape[0], dummy_data["num_classes"])

def test_compute_accuracy(dummy_data):
    """Test accuracy calculation."""
    # Create logits where we know the top prediction
    targets = dummy_data["targets"]
    logits = torch.zeros_like(dummy_data["logits"])
    logits[torch.arange(32), targets] = 1.0  # Make correct class highest
    
    acc = compute_accuracy(logits, targets)
    assert acc.item() == 1.0

def test_compute_accuracy_random(dummy_data):
    """Test that random logits yield accuracy > 0 (by chance) and < 1."""
    logits = torch.randn_like(dummy_data["logits"])
    acc = compute_accuracy(logits, dummy_data["targets"])
    assert 0.0 <= acc.item() <= 1.0
    # With 10 classes, random accuracy is ~0.1. It should not be 1.0.
    # (Probability of 1.0 by chance is extremely low for batch=32)
    assert acc.item() < 0.99

def test_linear_probe_training(dummy_data):
    """Test that LinearProbe can be trained to high accuracy on dummy data."""
    probe = LinearProbe(dummy_data["embedding_dim"], dummy_data["num_classes"])
    optimizer = torch.optim.Adam(probe.parameters(), lr=0.01)
    
    # Create a dataset where query maps perfectly to targets
    # We'll simulate this by setting query = target one-hot (roughly)
    # For this test, we just ensure the training loop runs and reduces loss
    query = dummy_data["query"]
    targets = dummy_data["targets"]
    
    initial_loss = None
    final_loss = None
    
    for epoch in range(10):
        optimizer.zero_grad()
        logits = probe(query)
        loss = torch.nn.functional.cross_entropy(logits, targets)
        loss.backward()
        optimizer.step()
        
        if epoch == 0:
            initial_loss = loss.item()
        if epoch == 9:
            final_loss = loss.item()
    
    # Loss should decrease over training
    assert final_loss < initial_loss

def test_linear_probe_accuracy_metric(dummy_data):
    """Test that LinearProbe accuracy can be measured correctly after training."""
    probe = LinearProbe(dummy_data["embedding_dim"], dummy_data["num_classes"])
    optimizer = torch.optim.Adam(probe.parameters(), lr=0.1)
    
    query = dummy_data["query"]
    targets = dummy_data["targets"]
    
    # Train for a few epochs to get reasonable accuracy
    for _ in range(20):
        optimizer.zero_grad()
        logits = probe(query)
        loss = torch.nn.functional.cross_entropy(logits, targets)
        loss.backward()
        optimizer.step()
    
    # Measure accuracy using the compute_accuracy helper
    logits = probe(query)
    acc = compute_accuracy(logits, targets)
    
    # After training, accuracy should be significantly better than random (0.1)
    # and ideally quite high, though we don't demand 1.0 for robustness
    assert acc.item() > 0.2

def test_info_nce_with_labels(dummy_data):
    """Test InfoNCE loss with positive/negative pairs logic."""
    # Simulate positive pairs (same index) and negatives (different indices)
    query = dummy_data["query"]
    key = dummy_data["key"]
    
    # Standard InfoNCE treats diagonal as positives
    loss = info_nce_loss(query, key)
    assert loss.item() >= 0.0

def test_compute_accuracy_edge_cases(dummy_data):
    """Test accuracy with edge cases like all same predictions."""
    targets = dummy_data["targets"]
    num_classes = dummy_data["num_classes"]
    
    # All predictions point to class 0
    logits = torch.zeros_like(dummy_data["logits"])
    logits[:, 0] = 1.0
    
    acc = compute_accuracy(logits, targets)
    # Accuracy is proportion of targets that are 0
    expected_acc = (targets == 0).float().mean().item()
    assert abs(acc.item() - expected_acc) < 1e-6