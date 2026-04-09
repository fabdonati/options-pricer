from __future__ import annotations

from math import erf, exp, log, sqrt

from options_pricer.models import OptionSpec


def norm_cdf(value: float) -> float:
    return 0.5 * (1.0 + erf(value / sqrt(2.0)))


def norm_pdf(value: float) -> float:
    return exp(-(value * value) / 2.0) / sqrt(2.0 * 3.141592653589793)


def d1(spec: OptionSpec) -> float:
    numerator = log(spec.spot / spec.strike) + (
        (spec.rate - spec.dividend_yield + 0.5 * spec.volatility**2) * spec.maturity
    )
    denominator = spec.volatility * sqrt(spec.maturity)
    return numerator / denominator


def d2(spec: OptionSpec) -> float:
    return d1(spec) - (spec.volatility * sqrt(spec.maturity))
