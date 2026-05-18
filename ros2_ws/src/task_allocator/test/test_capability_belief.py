import pytest

from task_allocator.capability_belief import CapabilityBelief


def test_initial_prior_preserved():
    belief = CapabilityBelief(mean=0.8, variance=0.1)
    assert belief.mean == pytest.approx(0.8)
    assert belief.variance == pytest.approx(0.1)


def test_invalid_variance_rejected():
    with pytest.raises(ValueError):
        CapabilityBelief(mean=0.5, variance=0.0)
    with pytest.raises(ValueError):
        CapabilityBelief(mean=0.5, variance=-1.0)


def test_invalid_obs_variance_rejected():
    belief = CapabilityBelief(mean=0.5, variance=1.0)
    with pytest.raises(ValueError):
        belief.update(observation=0.7, obs_variance=0.0)


def test_variance_reduces_on_observation():
    belief = CapabilityBelief(mean=0.5, variance=1.0)
    initial_variance = belief.variance
    belief.update(observation=0.7, obs_variance=1.0)
    assert belief.variance < initial_variance


def test_mean_pulled_toward_evidence():
    belief = CapabilityBelief(mean=0.0, variance=1.0)
    belief.update(observation=1.0, obs_variance=1.0)
    assert 0.0 < belief.mean < 1.0


def test_convergence_under_consistent_observations():
    belief = CapabilityBelief(mean=0.0, variance=10.0)
    for _ in range(50):
        belief.update(observation=1.0, obs_variance=0.1)
    assert belief.mean == pytest.approx(1.0, abs=0.01)
    assert belief.variance < 0.01
