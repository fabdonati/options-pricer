from __future__ import annotations

from math import exp

from options_pricer.black_scholes import black_scholes_price
from options_pricer.greeks import greeks
from options_pricer.models import OptionSpec


def implied_volatility(
    market_price: float,
    spec: OptionSpec,
    *,
    initial_guess: float = 0.2,
    tolerance: float = 1e-6,
    max_iterations: int = 50,
) -> float:
    if market_price <= _intrinsic_value(spec) + tolerance:
        return 0.0

    sigma = initial_guess
    for _ in range(max_iterations):
        trial_spec = OptionSpec(
            spot=spec.spot,
            strike=spec.strike,
            rate=spec.rate,
            volatility=sigma,
            maturity=spec.maturity,
            option_type=spec.option_type,
            dividend_yield=spec.dividend_yield,
        )
        price = black_scholes_price(trial_spec)
        diff = price - market_price
        if abs(diff) < tolerance:
            return sigma

        vega = greeks(trial_spec).vega
        if vega <= tolerance:
            return max(sigma, 0.0)
        sigma -= diff / vega
        sigma = max(sigma, tolerance)

    return sigma


def _intrinsic_value(spec: OptionSpec) -> float:
    discounted_spot = spec.spot * exp(-spec.dividend_yield * spec.maturity)
    discounted_strike = spec.strike * exp(-spec.rate * spec.maturity)
    if spec.option_type == "call":
        return max(discounted_spot - discounted_strike, 0.0)
    return max(discounted_strike - discounted_spot, 0.0)
