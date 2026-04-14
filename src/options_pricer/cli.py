from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

from options_pricer.binomial_tree import binomial_tree_price
from options_pricer.black_scholes import black_scholes_price
from options_pricer.implied_vol import implied_volatility
from options_pricer.models import OptionSpec, OptionType
from options_pricer.monte_carlo_report import (
    build_monte_carlo_report,
    render_monte_carlo_report,
    write_monte_carlo_report_chart,
    write_monte_carlo_report_csv,
)
from options_pricer.reporting import build_comparison_report, render_text_report, write_csv_report
from options_pricer.sweep import run_sweep, write_sweep_csv


def main() -> None:
    parser = argparse.ArgumentParser(prog="optprice", description="Vanilla option pricing CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_common_option_args(subparsers.add_parser("price", help="Price an option"))
    iv_parser = _add_common_option_args(
        subparsers.add_parser("iv", help="Infer implied volatility from a market price")
    )
    iv_parser.add_argument("--market-price", type=float, required=True)
    tree_parser = _add_common_option_args(
        subparsers.add_parser("tree", help="Price an option with a binomial tree")
    )
    tree_parser.add_argument("--steps", type=int, default=200)
    compare_parser = _add_common_option_args(
        subparsers.add_parser(
            "compare",
            help="Compare Black-Scholes, binomial tree, and Monte Carlo prices",
        )
    )
    compare_parser.add_argument("--steps", type=int, default=200)
    compare_parser.add_argument("--paths", type=int, default=20_000)
    compare_parser.add_argument("--seed", type=int, default=42)
    compare_parser.add_argument("--market-price", type=float)
    compare_parser.add_argument("--report-output", type=Path)
    sweep_parser = _add_common_option_args(
        subparsers.add_parser(
            "sweep",
            help="Sweep spot or volatility and export a model comparison table",
        )
    )
    sweep_parser.add_argument("--axis", choices=("spot", "volatility"), required=True)
    sweep_parser.add_argument("--start", type=float, required=True)
    sweep_parser.add_argument("--stop", type=float, required=True)
    sweep_parser.add_argument("--points", type=int, required=True)
    sweep_parser.add_argument("--steps", type=int, default=200)
    sweep_parser.add_argument("--paths", type=int, default=20_000)
    sweep_parser.add_argument("--seed", type=int, default=42)
    sweep_parser.add_argument("--output", type=Path, required=True)
    mc_report_parser = _add_common_option_args(
        subparsers.add_parser(
            "mc-report",
            help="Run Monte Carlo convergence diagnostics across multiple path counts",
        )
    )
    mc_report_parser.add_argument("--path-grid", required=True)
    mc_report_parser.add_argument("--seed", type=int, default=42)
    mc_report_parser.add_argument("--report-output", type=Path, required=True)
    mc_report_parser.add_argument("--chart-output", type=Path)

    args = parser.parse_args()
    spec = _spec_from_args(args)

    if args.command == "price":
        print(f"{black_scholes_price(spec):.6f}")
    elif args.command == "iv":
        print(f"{implied_volatility(args.market_price, spec):.6f}")
    elif args.command == "tree":
        print(f"{binomial_tree_price(spec, steps=args.steps):.6f}")
    elif args.command == "sweep":
        rows = run_sweep(
            spec,
            axis=args.axis,
            start=args.start,
            stop=args.stop,
            points=args.points,
            tree_steps=args.steps,
            monte_carlo_paths=args.paths,
            monte_carlo_seed=args.seed,
        )
        write_sweep_csv(rows, args.output)
        print(
            f"Wrote {len(rows)} sweep rows to {args.output} "
            f"for axis={args.axis} over [{args.start}, {args.stop}]"
        )
    elif args.command == "mc-report":
        mc_report = build_monte_carlo_report(
            spec,
            path_counts=_parse_path_grid(args.path_grid),
            seed=args.seed,
        )
        write_monte_carlo_report_csv(mc_report, args.report_output)
        if args.chart_output is not None:
            write_monte_carlo_report_chart(mc_report, args.chart_output)
        print(render_monte_carlo_report(mc_report))
        print(f"\nWrote Monte Carlo diagnostics CSV to {args.report_output}")
        if args.chart_output is not None:
            print(f"Wrote Monte Carlo diagnostics chart to {args.chart_output}")
    else:
        comparison_report = build_comparison_report(
            spec,
            tree_steps=args.steps,
            monte_carlo_paths=args.paths,
            monte_carlo_seed=args.seed,
            market_price=args.market_price,
        )
        if args.report_output is not None:
            write_csv_report(comparison_report, args.report_output)
        print(render_text_report(comparison_report))


def _add_common_option_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--spot", type=float, required=True)
    parser.add_argument("--strike", type=float, required=True)
    parser.add_argument("--rate", type=float, required=True)
    parser.add_argument("--dividend-yield", type=float, default=0.0)
    parser.add_argument("--volatility", type=float, required=True)
    parser.add_argument("--maturity", type=float, required=True)
    parser.add_argument("--type", choices=("call", "put"), required=True)
    return parser


def _spec_from_args(args: argparse.Namespace) -> OptionSpec:
    option_type = args.type
    return OptionSpec(
        spot=args.spot,
        strike=args.strike,
        rate=args.rate,
        dividend_yield=args.dividend_yield,
        volatility=args.volatility,
        maturity=args.maturity,
        option_type=_as_option_type(option_type),
    )


def _as_option_type(option_type: str) -> OptionType:
    if option_type not in {"call", "put"}:
        raise ValueError("option type must be 'call' or 'put'")
    return cast(OptionType, option_type)


def _parse_path_grid(path_grid: str) -> list[int]:
    values = [value.strip() for value in path_grid.split(",")]
    if any(not value for value in values):
        raise ValueError("path grid entries must not be empty")
    return [int(value) for value in values]


if __name__ == "__main__":
    main()
