from __future__ import annotations

import argparse
from typing import cast

from options_pricer.binomial_tree import binomial_tree_price
from options_pricer.black_scholes import black_scholes_price
from options_pricer.implied_vol import implied_volatility
from options_pricer.models import OptionSpec, OptionType
from options_pricer.monte_carlo import monte_carlo_price


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

    args = parser.parse_args()
    spec = _spec_from_args(args)

    if args.command == "price":
        print(f"{black_scholes_price(spec):.6f}")
    elif args.command == "iv":
        print(f"{implied_volatility(args.market_price, spec):.6f}")
    elif args.command == "tree":
        print(f"{binomial_tree_price(spec, steps=args.steps):.6f}")
    else:
        analytic = black_scholes_price(spec)
        tree_price = binomial_tree_price(spec, steps=args.steps)
        simulated = monte_carlo_price(spec, paths=args.paths)
        print(f"Black-Scholes: {analytic:.6f}")
        print(f"Binomial tree: {tree_price:.6f}")
        print(f"Monte Carlo: {simulated:.6f}")
        print(f"Tree - Black-Scholes: {tree_price - analytic:.6f}")
        print(f"Monte Carlo - Black-Scholes: {simulated - analytic:.6f}")


def _add_common_option_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("--spot", type=float, required=True)
    parser.add_argument("--strike", type=float, required=True)
    parser.add_argument("--rate", type=float, required=True)
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
