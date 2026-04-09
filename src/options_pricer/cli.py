from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

from options_pricer.binomial_tree import binomial_tree_price
from options_pricer.black_scholes import black_scholes_price
from options_pricer.implied_vol import implied_volatility
from options_pricer.models import OptionSpec, OptionType
from options_pricer.reporting import build_comparison_report, render_text_report, write_csv_report


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

    args = parser.parse_args()
    spec = _spec_from_args(args)

    if args.command == "price":
        print(f"{black_scholes_price(spec):.6f}")
    elif args.command == "iv":
        print(f"{implied_volatility(args.market_price, spec):.6f}")
    elif args.command == "tree":
        print(f"{binomial_tree_price(spec, steps=args.steps):.6f}")
    else:
        report = build_comparison_report(
            spec,
            tree_steps=args.steps,
            monte_carlo_paths=args.paths,
            monte_carlo_seed=args.seed,
            market_price=args.market_price,
        )
        if args.report_output is not None:
            write_csv_report(report, args.report_output)
        print(render_text_report(report))


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


if __name__ == "__main__":
    main()
