from __future__ import annotations

from math import exp

from options_pricer.common import d1, d2, norm_cdf
from options_pricer.models import OptionSpec


def black_scholes_price(spec: OptionSpec) -> float:
    d1_value = d1(spec)
    d2_value = d2(spec)
    discounted_spot = spec.spot * exp(-spec.dividend_yield * spec.maturity)
    discounted_strike = spec.strike * exp(-spec.rate * spec.maturity)

    if spec.option_type == "call":
        return (discounted_spot * norm_cdf(d1_value)) - (discounted_strike * norm_cdf(d2_value))

    return (discounted_strike * norm_cdf(-d2_value)) - (discounted_spot * norm_cdf(-d1_value))
