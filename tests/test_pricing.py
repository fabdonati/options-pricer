from __future__ import annotations

import pytest

from options_pricer.binomial_tree import binomial_tree_price
from options_pricer.black_scholes import black_scholes_price
from options_pricer.greeks import greeks
from options_pricer.implied_vol import implied_volatility
from options_pricer.models import OptionSpec
from options_pricer.monte_carlo import monte_carlo_price


@pytest.fixture
def vanilla_call() -> OptionSpec:
    return OptionSpec(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.2,
        maturity=1.0,
        option_type="call",
    )


def test_black_scholes_price_matches_reference_value(vanilla_call: OptionSpec) -> None:
    assert black_scholes_price(vanilla_call) == pytest.approx(10.450583572185565)


def test_greeks_match_reference_values(vanilla_call: OptionSpec) -> None:
    result = greeks(vanilla_call)

    assert result.delta == pytest.approx(0.6368306512, rel=1e-6)
    assert result.gamma == pytest.approx(0.0187620173, rel=1e-6)
    assert result.vega == pytest.approx(37.52403469, rel=1e-6)
    assert result.theta == pytest.approx(-6.41402755, rel=1e-6)
    assert result.rho == pytest.approx(53.23248155, rel=1e-6)


def test_implied_volatility_round_trips_market_price(vanilla_call: OptionSpec) -> None:
    market_price = black_scholes_price(vanilla_call)

    implied_vol = implied_volatility(market_price, vanilla_call, initial_guess=0.3)

    assert implied_vol == pytest.approx(0.2, rel=1e-6)


def test_monte_carlo_tracks_analytic_price(vanilla_call: OptionSpec) -> None:
    analytic_price = black_scholes_price(vanilla_call)
    simulated_price = monte_carlo_price(vanilla_call, paths=25_000, seed=7)

    assert simulated_price == pytest.approx(analytic_price, abs=0.35)


def test_binomial_tree_tracks_analytic_price_for_call(vanilla_call: OptionSpec) -> None:
    analytic_price = black_scholes_price(vanilla_call)
    tree_price = binomial_tree_price(vanilla_call, steps=200)

    assert tree_price == pytest.approx(analytic_price, abs=0.05)


def test_binomial_tree_tracks_analytic_price_for_put() -> None:
    put = OptionSpec(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.2,
        maturity=1.0,
        option_type="put",
    )

    analytic_price = black_scholes_price(put)
    tree_price = binomial_tree_price(put, steps=200)

    assert tree_price == pytest.approx(analytic_price, abs=0.05)


def test_binomial_tree_converges_toward_black_scholes(vanilla_call: OptionSpec) -> None:
    analytic_price = black_scholes_price(vanilla_call)
    coarse_error = abs(binomial_tree_price(vanilla_call, steps=25) - analytic_price)
    fine_error = abs(binomial_tree_price(vanilla_call, steps=200) - analytic_price)

    assert fine_error < coarse_error


def test_binomial_tree_rejects_non_positive_step_counts(vanilla_call: OptionSpec) -> None:
    with pytest.raises(ValueError, match="steps must be positive"):
        binomial_tree_price(vanilla_call, steps=0)


def test_implied_volatility_returns_zero_for_intrinsic_value_prices() -> None:
    spec = OptionSpec(
        spot=100.0,
        strike=150.0,
        rate=0.01,
        volatility=0.2,
        maturity=0.05,
        option_type="call",
    )

    assert black_scholes_price(spec) == 0.0
    assert implied_volatility(0.0, spec, initial_guess=1.5) == pytest.approx(0.0)
