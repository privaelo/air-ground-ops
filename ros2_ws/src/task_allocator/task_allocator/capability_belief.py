class CapabilityBelief:
    """Bayesian Gaussian belief over a scalar robot capability."""

    def __init__(self, mean: float, variance: float) -> None:
        if variance <= 0:
            raise ValueError(f"variance must be positive, got {variance}")
        self._mean = float(mean)
        self._variance = float(variance)

    @property
    def mean(self) -> float:
        return self._mean

    @property
    def variance(self) -> float:
        return self._variance

    def update(self, observation: float, obs_variance: float) -> None:
        """Gaussian conjugate-prior update (information-form)."""
        if obs_variance <= 0:
            raise ValueError(f"obs_variance must be positive, got {obs_variance}")
        prior_prec = 1.0 / self._variance
        obs_prec = 1.0 / obs_variance
        new_prec = prior_prec + obs_prec
        self._variance = 1.0 / new_prec
        self._mean = self._variance * (prior_prec * self._mean + obs_prec * observation)
