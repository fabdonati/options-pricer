from __future__ import annotations

import random
from dataclasses import dataclass
from math import exp, sqrt

from options_pricer.models import OptionSpec


@dataclass(frozen=True, slots=True)
class MonteCarloEstimate:
    price: float
    sample_variance: float
    standard_error: float
    ci_lower_95: float
    ci_upper_95: float
    paths: int
    seed: int


def monte_carlo_price(spec: OptionSpec, *, paths: int = 10_000, seed: int = 42) -> float:
    return monte_carlo_estimate(spec, paths=paths, seed=seed).price


def monte_carlo_estimate(
    spec: OptionSpec,
    *,
    paths: int = 10_000,
    seed: int = 42,
) -> MonteCarloEstimate:
    if paths <= 1:
        raise ValueError("paths must be greater than 1")

    rng = random.Random(seed)
    drift = (spec.rate - spec.dividend_yield - 0.5 * spec.volatility**2) * spec.maturity
    diffusion_scale = spec.volatility * sqrt(spec.maturity)
    discount_factor = exp(-spec.rate * spec.maturity)
    discounted_payoffs: list[float] = []

    for _ in range(paths):
        shock = rng.gauss(0.0, 1.0)
        terminal_spot = spec.spot * exp(drift + diffusion_scale * shock)
        if spec.option_type == "call":
            payoff = max(terminal_spot - spec.strike, 0.0)
        else:
            payoff = max(spec.strike - terminal_spot, 0.0)
        discounted_payoffs.append(discount_factor * payoff)

    mean_payoff = sum(discounted_payoffs) / paths
    squared_deviations = sum((payoff - mean_payoff) ** 2 for payoff in discounted_payoffs)
    sample_variance = squared_deviations / (paths - 1)
    standard_error = sqrt(sample_variance / paths)
    confidence_radius = 1.96 * standard_error

    return MonteCarloEstimate(
        price=mean_payoff,
        sample_variance=sample_variance,
        standard_error=standard_error,
        ci_lower_95=mean_payoff - confidence_radius,
        ci_upper_95=mean_payoff + confidence_radius,
        paths=paths,
        seed=seed,
    )
