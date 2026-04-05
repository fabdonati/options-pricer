from __future__ import annotations

import pytest

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
