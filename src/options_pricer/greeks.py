from __future__ import annotations

from dataclasses import dataclass
from math import exp, sqrt

from options_pricer.common import d1, d2, norm_cdf, norm_pdf
from options_pricer.models import OptionSpec


@dataclass(frozen=True, slots=True)
class Greeks:
    delta: float
    gamma: float
    vega: float
    theta: float
    rho: float


def greeks(spec: OptionSpec) -> Greeks:
    d1_value = d1(spec)
    d2_value = d2(spec)
    sqrt_t = sqrt(spec.maturity)
    pdf = norm_pdf(d1_value)
    discounted_strike = spec.strike * exp(-spec.rate * spec.maturity)

    gamma = pdf / (spec.spot * spec.volatility * sqrt_t)
    vega = spec.spot * pdf * sqrt_t

    if spec.option_type == "call":
        delta = norm_cdf(d1_value)
        theta = (
            -(spec.spot * pdf * spec.volatility) / (2.0 * sqrt_t)
            - spec.rate * discounted_strike * norm_cdf(d2_value)
        )
        rho = spec.strike * spec.maturity * exp(-spec.rate * spec.maturity) * norm_cdf(d2_value)
    else:
        delta = norm_cdf(d1_value) - 1.0
        theta = (
            -(spec.spot * pdf * spec.volatility) / (2.0 * sqrt_t)
            + spec.rate * discounted_strike * norm_cdf(-d2_value)
        )
        rho = -spec.strike * spec.maturity * exp(-spec.rate * spec.maturity) * norm_cdf(-d2_value)

    return Greeks(delta=delta, gamma=gamma, vega=vega, theta=theta, rho=rho)
