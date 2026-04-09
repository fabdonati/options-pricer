from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from options_pricer.binomial_tree import binomial_tree_price
from options_pricer.black_scholes import black_scholes_price
from options_pricer.greeks import Greeks, greeks
from options_pricer.implied_vol import implied_volatility
from options_pricer.models import OptionSpec
from options_pricer.monte_carlo import monte_carlo_price


@dataclass(frozen=True, slots=True)
class PriceComparison:
    model: str
    price: float
    absolute_error_vs_black_scholes: float
    relative_error_vs_black_scholes: float
    runtime_ms: float


@dataclass(frozen=True, slots=True)
class MarketComparison:
    market_price: float
    implied_volatility: float
    residual_vs_black_scholes: float
    residual_vs_binomial_tree: float
    residual_vs_monte_carlo: float


@dataclass(frozen=True, slots=True)
class ComparisonReport:
    spec: OptionSpec
    tree_steps: int
    monte_carlo_paths: int
    monte_carlo_seed: int
    price_rows: tuple[PriceComparison, ...]
    analytic_greeks: Greeks
    market_comparison: MarketComparison | None = None


def build_comparison_report(
    spec: OptionSpec,
    *,
    tree_steps: int,
    monte_carlo_paths: int,
    monte_carlo_seed: int = 42,
    market_price: float | None = None,
) -> ComparisonReport:
    analytic_price, analytic_runtime = _timed_call(lambda: black_scholes_price(spec))
    tree_price, tree_runtime = _timed_call(lambda: binomial_tree_price(spec, steps=tree_steps))
    monte_carlo_result, monte_carlo_runtime = _timed_call(
        lambda: monte_carlo_price(spec, paths=monte_carlo_paths, seed=monte_carlo_seed)
    )

    price_rows = (
        PriceComparison(
            model="Black-Scholes",
            price=analytic_price,
            absolute_error_vs_black_scholes=0.0,
            relative_error_vs_black_scholes=0.0,
            runtime_ms=analytic_runtime,
        ),
        PriceComparison(
            model="Binomial tree",
            price=tree_price,
            absolute_error_vs_black_scholes=abs(tree_price - analytic_price),
            relative_error_vs_black_scholes=_relative_error(tree_price, analytic_price),
            runtime_ms=tree_runtime,
        ),
        PriceComparison(
            model="Monte Carlo",
            price=monte_carlo_result,
            absolute_error_vs_black_scholes=abs(monte_carlo_result - analytic_price),
            relative_error_vs_black_scholes=_relative_error(monte_carlo_result, analytic_price),
            runtime_ms=monte_carlo_runtime,
        ),
    )

    market_comparison: MarketComparison | None = None
    if market_price is not None:
        market_comparison = MarketComparison(
            market_price=market_price,
            implied_volatility=implied_volatility(market_price, spec),
            residual_vs_black_scholes=market_price - analytic_price,
            residual_vs_binomial_tree=market_price - tree_price,
            residual_vs_monte_carlo=market_price - monte_carlo_result,
        )

    return ComparisonReport(
        spec=spec,
        tree_steps=tree_steps,
        monte_carlo_paths=monte_carlo_paths,
        monte_carlo_seed=monte_carlo_seed,
        price_rows=price_rows,
        analytic_greeks=greeks(spec),
        market_comparison=market_comparison,
    )


def render_text_report(report: ComparisonReport) -> str:
    lines = [
        "Contract",
        f"Spot: {report.spec.spot:.6f}",
        f"Strike: {report.spec.strike:.6f}",
        f"Rate: {report.spec.rate:.6f}",
        f"Dividend yield: {report.spec.dividend_yield:.6f}",
        f"Volatility: {report.spec.volatility:.6f}",
        f"Maturity: {report.spec.maturity:.6f}",
        f"Type: {report.spec.option_type}",
        f"Tree steps: {report.tree_steps}",
        f"Monte Carlo paths: {report.monte_carlo_paths}",
        f"Monte Carlo seed: {report.monte_carlo_seed}",
        "",
        "Price Comparison",
        "Model           Price       Abs Error   Rel Error   Runtime (ms)",
    ]

    for row in report.price_rows:
        lines.append(
            f"{row.model:<15} "
            f"{row.price:>10.6f} "
            f"{row.absolute_error_vs_black_scholes:>11.6f} "
            f"{row.relative_error_vs_black_scholes:>11.6f} "
            f"{row.runtime_ms:>12.3f}"
        )

    lines.extend(
        [
            "",
            "Analytic Greeks",
            f"Delta: {report.analytic_greeks.delta:.6f}",
            f"Gamma: {report.analytic_greeks.gamma:.6f}",
            f"Vega: {report.analytic_greeks.vega:.6f}",
            f"Theta: {report.analytic_greeks.theta:.6f}",
            f"Rho: {report.analytic_greeks.rho:.6f}",
        ]
    )

    if report.market_comparison is not None:
        lines.extend(
            [
                "",
                "Market",
                f"Market price: {report.market_comparison.market_price:.6f}",
                f"Implied volatility: {report.market_comparison.implied_volatility:.6f}",
                (
                    "Market - Black-Scholes: "
                    f"{report.market_comparison.residual_vs_black_scholes:.6f}"
                ),
                (
                    "Market - Binomial tree: "
                    f"{report.market_comparison.residual_vs_binomial_tree:.6f}"
                ),
                (
                    "Market - Monte Carlo: "
                    f"{report.market_comparison.residual_vs_monte_carlo:.6f}"
                ),
            ]
        )

    return "\n".join(lines)


def write_csv_report(report: ComparisonReport, destination: str | Path) -> None:
    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["section", "name", "value"])

        _write_contract_rows(writer, report)
        _write_price_rows(writer, report)
        _write_greek_rows(writer, report)
        _write_market_rows(writer, report)


def _write_contract_rows(writer: Any, report: ComparisonReport) -> None:
    contract_values = {
        "spot": report.spec.spot,
        "strike": report.spec.strike,
        "rate": report.spec.rate,
        "dividend_yield": report.spec.dividend_yield,
        "volatility": report.spec.volatility,
        "maturity": report.spec.maturity,
        "type": report.spec.option_type,
        "tree_steps": report.tree_steps,
        "monte_carlo_paths": report.monte_carlo_paths,
        "monte_carlo_seed": report.monte_carlo_seed,
    }
    for name, value in contract_values.items():
        writer.writerow(["contract", name, value])


def _write_price_rows(writer: Any, report: ComparisonReport) -> None:
    for row in report.price_rows:
        section_name = f"price:{_section_slug(row.model)}"
        writer.writerow([section_name, "price", row.price])
        writer.writerow(
            [section_name, "abs_error_vs_black_scholes", row.absolute_error_vs_black_scholes]
        )
        writer.writerow(
            [section_name, "relative_error_vs_black_scholes", row.relative_error_vs_black_scholes]
        )
        writer.writerow([section_name, "runtime_ms", row.runtime_ms])


def _write_greek_rows(writer: Any, report: ComparisonReport) -> None:
    greek_values = {
        "delta": report.analytic_greeks.delta,
        "gamma": report.analytic_greeks.gamma,
        "vega": report.analytic_greeks.vega,
        "theta": report.analytic_greeks.theta,
        "rho": report.analytic_greeks.rho,
    }
    for name, value in greek_values.items():
        writer.writerow(["greeks", name, value])


def _write_market_rows(writer: Any, report: ComparisonReport) -> None:
    if report.market_comparison is None:
        return

    writer.writerow(["market", "market_price", report.market_comparison.market_price])
    writer.writerow(
        ["market", "implied_volatility", report.market_comparison.implied_volatility]
    )
    writer.writerow(
        ["market", "residual_vs_black_scholes", report.market_comparison.residual_vs_black_scholes]
    )
    writer.writerow(
        ["market", "residual_vs_binomial_tree", report.market_comparison.residual_vs_binomial_tree]
    )
    writer.writerow(
        ["market", "residual_vs_monte_carlo", report.market_comparison.residual_vs_monte_carlo]
    )


def _timed_call(function: Callable[[], float]) -> tuple[float, float]:
    start = perf_counter()
    value = function()
    elapsed_ms = (perf_counter() - start) * 1_000.0
    return value, elapsed_ms


def _relative_error(value: float, reference: float) -> float:
    if reference == 0.0:
        return 0.0 if value == 0.0 else float("inf")
    return abs(value - reference) / abs(reference)


def _section_slug(value: str) -> str:
    return value.lower().replace("-", "_").replace(" ", "_")
