from __future__ import annotations

from math import exp, sqrt

from options_pricer.models import OptionSpec


def binomial_tree_price(spec: OptionSpec, *, steps: int = 200) -> float:
    if steps <= 0:
        raise ValueError("steps must be positive")
    if spec.maturity <= 0.0:
        return _payoff(spec.spot, spec.strike, spec.option_type)
    if spec.volatility <= 0.0:
        terminal_spot = spec.spot * exp(spec.rate * spec.maturity)
        payoff = _payoff(terminal_spot, spec.strike, spec.option_type)
        return exp(-spec.rate * spec.maturity) * payoff

    dt = spec.maturity / steps
    up = exp(spec.volatility * sqrt(dt))
    down = 1.0 / up
    discount = exp(-spec.rate * dt)
    probability = (exp(spec.rate * dt) - down) / (up - down)

    values = [
        _payoff(
            spec.spot * (up ** (steps - downs)) * (down**downs),
            spec.strike,
            spec.option_type,
        )
        for downs in range(steps + 1)
    ]

    for step in range(steps - 1, -1, -1):
        values = [
            discount * (probability * values[node] + (1.0 - probability) * values[node + 1])
            for node in range(step + 1)
        ]

    return values[0]


def _payoff(spot: float, strike: float, option_type: str) -> float:
    if option_type == "call":
        return max(spot - strike, 0.0)
    return max(strike - spot, 0.0)
