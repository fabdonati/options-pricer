from __future__ import annotations

import random
from math import exp, sqrt

from options_pricer.models import OptionSpec


def monte_carlo_price(spec: OptionSpec, *, paths: int = 10_000, seed: int = 42) -> float:
    rng = random.Random(seed)
    drift = (spec.rate - 0.5 * spec.volatility**2) * spec.maturity
    diffusion_scale = spec.volatility * sqrt(spec.maturity)
    discounted_payoff = 0.0

    for _ in range(paths):
        shock = rng.gauss(0.0, 1.0)
        terminal_spot = spec.spot * exp(drift + diffusion_scale * shock)
        if spec.option_type == "call":
            payoff = max(terminal_spot - spec.strike, 0.0)
        else:
            payoff = max(spec.strike - terminal_spot, 0.0)
        discounted_payoff += payoff

    return exp(-spec.rate * spec.maturity) * (discounted_payoff / paths)
