from __future__ import annotations

from pathlib import Path

import pytest

from options_pricer.binomial_tree import binomial_tree_price
from options_pricer.black_scholes import black_scholes_price
from options_pricer.greeks import greeks
from options_pricer.implied_vol import implied_volatility
from options_pricer.models import OptionSpec
from options_pricer.monte_carlo import monte_carlo_estimate, monte_carlo_price
from options_pricer.monte_carlo_report import (
    build_monte_carlo_report,
    write_monte_carlo_report_chart,
)
from options_pricer.reporting import build_comparison_report
from options_pricer.sweep import run_sweep


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


def test_black_scholes_price_supports_dividend_yield() -> None:
    spec = OptionSpec(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.2,
        maturity=1.0,
        option_type="call",
        dividend_yield=0.02,
    )

    assert black_scholes_price(spec) == pytest.approx(9.227005508154036)


def test_greeks_match_reference_values(vanilla_call: OptionSpec) -> None:
    result = greeks(vanilla_call)

    assert result.delta == pytest.approx(0.6368306512, rel=1e-6)
    assert result.gamma == pytest.approx(0.0187620173, rel=1e-6)
    assert result.vega == pytest.approx(37.52403469, rel=1e-6)
    assert result.theta == pytest.approx(-6.41402755, rel=1e-6)
    assert result.rho == pytest.approx(53.23248155, rel=1e-6)


def test_greeks_support_dividend_yield() -> None:
    spec = OptionSpec(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.2,
        maturity=1.0,
        option_type="call",
        dividend_yield=0.02,
    )

    result = greeks(spec)

    assert result.delta == pytest.approx(0.5868511461, rel=1e-6)
    assert result.gamma == pytest.approx(0.0189505788, rel=1e-6)
    assert result.vega == pytest.approx(37.90115751, rel=1e-6)
    assert result.theta == pytest.approx(-5.089318914, rel=1e-6)
    assert result.rho == pytest.approx(49.458109105, rel=1e-6)


def test_implied_volatility_round_trips_market_price(vanilla_call: OptionSpec) -> None:
    market_price = black_scholes_price(vanilla_call)

    implied_vol = implied_volatility(market_price, vanilla_call, initial_guess=0.3)

    assert implied_vol == pytest.approx(0.2, rel=1e-6)


def test_implied_volatility_round_trips_with_dividend_yield() -> None:
    spec = OptionSpec(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.2,
        maturity=1.0,
        option_type="call",
        dividend_yield=0.02,
    )

    market_price = black_scholes_price(spec)
    implied_vol = implied_volatility(market_price, spec, initial_guess=0.3)

    assert implied_vol == pytest.approx(0.2, rel=1e-6)


def test_monte_carlo_tracks_analytic_price(vanilla_call: OptionSpec) -> None:
    analytic_price = black_scholes_price(vanilla_call)
    simulated_price = monte_carlo_price(vanilla_call, paths=25_000, seed=7)

    assert simulated_price == pytest.approx(analytic_price, abs=0.35)


def test_monte_carlo_tracks_dividend_adjusted_analytic_price() -> None:
    spec = OptionSpec(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.2,
        maturity=1.0,
        option_type="call",
        dividend_yield=0.02,
    )

    analytic_price = black_scholes_price(spec)
    simulated_price = monte_carlo_price(spec, paths=25_000, seed=7)

    assert simulated_price == pytest.approx(analytic_price, abs=0.35)


def test_monte_carlo_estimate_includes_confidence_interval(vanilla_call: OptionSpec) -> None:
    estimate = monte_carlo_estimate(vanilla_call, paths=5_000, seed=7)

    assert estimate.ci_lower_95 < estimate.price < estimate.ci_upper_95
    assert estimate.sample_variance > 0.0
    assert estimate.standard_error > 0.0


def test_binomial_tree_tracks_analytic_price_for_call(vanilla_call: OptionSpec) -> None:
    analytic_price = black_scholes_price(vanilla_call)
    tree_price = binomial_tree_price(vanilla_call, steps=200)

    assert tree_price == pytest.approx(analytic_price, abs=0.05)


def test_binomial_tree_tracks_dividend_adjusted_analytic_price() -> None:
    spec = OptionSpec(
        spot=100.0,
        strike=100.0,
        rate=0.05,
        volatility=0.2,
        maturity=1.0,
        option_type="call",
        dividend_yield=0.02,
    )

    analytic_price = black_scholes_price(spec)
    tree_price = binomial_tree_price(spec, steps=200)

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


def test_comparison_report_uses_black_scholes_as_baseline(vanilla_call: OptionSpec) -> None:
    report = build_comparison_report(
        vanilla_call,
        tree_steps=150,
        monte_carlo_paths=5_000,
        monte_carlo_seed=7,
    )

    assert report.price_rows[0].model == "Black-Scholes"
    assert report.monte_carlo_seed == 7
    assert report.price_rows[0].absolute_error_vs_black_scholes == 0.0
    assert report.price_rows[0].relative_error_vs_black_scholes == 0.0
    assert report.price_rows[1].absolute_error_vs_black_scholes >= 0.0
    assert report.price_rows[1].relative_error_vs_black_scholes >= 0.0
    assert report.price_rows[2].absolute_error_vs_black_scholes >= 0.0
    assert report.price_rows[2].relative_error_vs_black_scholes >= 0.0


def test_comparison_report_market_section_round_trips_implied_vol(
    vanilla_call: OptionSpec,
) -> None:
    market_price = black_scholes_price(vanilla_call)
    report = build_comparison_report(
        vanilla_call,
        tree_steps=150,
        monte_carlo_paths=5_000,
        monte_carlo_seed=7,
        market_price=market_price,
    )

    assert report.market_comparison is not None
    assert report.market_comparison.implied_volatility == pytest.approx(0.2, rel=1e-6)
    assert report.market_comparison.residual_vs_black_scholes == pytest.approx(0.0, abs=1e-9)


def test_run_sweep_supports_spot_axis(vanilla_call: OptionSpec) -> None:
    rows = run_sweep(
        vanilla_call,
        axis="spot",
        start=90.0,
        stop=110.0,
        points=3,
        tree_steps=150,
        monte_carlo_paths=5_000,
        monte_carlo_seed=7,
    )

    assert [row.value for row in rows] == pytest.approx([90.0, 100.0, 110.0])
    assert rows[0].axis == "spot"
    assert rows[1].black_scholes == pytest.approx(10.450583572185565)
    assert rows[1].binomial_tree == pytest.approx(rows[1].black_scholes, abs=0.1)


def test_run_sweep_is_reproducible_for_same_seed(vanilla_call: OptionSpec) -> None:
    first = run_sweep(
        vanilla_call,
        axis="volatility",
        start=0.15,
        stop=0.25,
        points=3,
        tree_steps=150,
        monte_carlo_paths=5_000,
        monte_carlo_seed=7,
    )
    second = run_sweep(
        vanilla_call,
        axis="volatility",
        start=0.15,
        stop=0.25,
        points=3,
        tree_steps=150,
        monte_carlo_paths=5_000,
        monte_carlo_seed=7,
    )

    assert first == second


def test_monte_carlo_report_rows_capture_convergence(vanilla_call: OptionSpec) -> None:
    report = build_monte_carlo_report(vanilla_call, path_counts=[1_000, 5_000, 20_000], seed=7)

    assert [row.paths for row in report.rows] == [1_000, 5_000, 20_000]
    assert (
        report.rows[0].ci_lower_95
        < report.rows[0].monte_carlo_price
        < report.rows[0].ci_upper_95
    )
    assert report.rows[-1].standard_error < report.rows[0].standard_error
    assert report.rows[-1].black_scholes_price == pytest.approx(10.450583572185565)


def test_monte_carlo_report_chart_writes_svg(tmp_path: Path, vanilla_call: OptionSpec) -> None:
    report = build_monte_carlo_report(vanilla_call, path_counts=[1_000, 5_000, 20_000], seed=7)
    chart_path = tmp_path / "mc_report.svg"

    write_monte_carlo_report_chart(report, chart_path)

    contents = chart_path.read_text(encoding="utf-8")
    assert contents.startswith("<svg")
    assert "Monte Carlo convergence diagnostics" in contents
