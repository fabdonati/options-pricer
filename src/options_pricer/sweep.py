from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

from options_pricer.binomial_tree import binomial_tree_price
from options_pricer.black_scholes import black_scholes_price
from options_pricer.models import OptionSpec
from options_pricer.monte_carlo import monte_carlo_price

SweepAxis = Literal["spot", "volatility"]


@dataclass(frozen=True, slots=True)
class SweepRow:
    axis: SweepAxis
    value: float
    black_scholes: float
    binomial_tree: float
    monte_carlo: float
    tree_error_vs_black_scholes: float
    monte_carlo_error_vs_black_scholes: float


def run_sweep(
    spec: OptionSpec,
    *,
    axis: SweepAxis,
    start: float,
    stop: float,
    points: int,
    tree_steps: int,
    monte_carlo_paths: int,
    monte_carlo_seed: int,
) -> list[SweepRow]:
    if points < 2:
        raise ValueError("points must be at least 2")
    if start >= stop:
        raise ValueError("start must be less than stop")

    values = _linspace(start, stop, points)
    rows: list[SweepRow] = []
    for index, value in enumerate(values):
        row_spec = _spec_for_axis(spec, axis=axis, value=value)
        analytic = black_scholes_price(row_spec)
        tree = binomial_tree_price(row_spec, steps=tree_steps)
        monte_carlo = monte_carlo_price(
            row_spec,
            paths=monte_carlo_paths,
            seed=monte_carlo_seed + index,
        )
        rows.append(
            SweepRow(
                axis=axis,
                value=value,
                black_scholes=analytic,
                binomial_tree=tree,
                monte_carlo=monte_carlo,
                tree_error_vs_black_scholes=tree - analytic,
                monte_carlo_error_vs_black_scholes=monte_carlo - analytic,
            )
        )
    return rows


def write_sweep_csv(rows: list[SweepRow], destination: str | Path) -> None:
    if not rows:
        raise ValueError("rows must not be empty")

    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "axis",
                "value",
                "black_scholes",
                "binomial_tree",
                "monte_carlo",
                "tree_error_vs_black_scholes",
                "monte_carlo_error_vs_black_scholes",
            ]
        )
        for row in rows:
            writer.writerow(
                [
                    row.axis,
                    row.value,
                    row.black_scholes,
                    row.binomial_tree,
                    row.monte_carlo,
                    row.tree_error_vs_black_scholes,
                    row.monte_carlo_error_vs_black_scholes,
                ]
            )


def _linspace(start: float, stop: float, points: int) -> list[float]:
    step = (stop - start) / (points - 1)
    return [start + step * index for index in range(points)]


def _spec_for_axis(spec: OptionSpec, *, axis: SweepAxis, value: float) -> OptionSpec:
    if axis == "spot":
        return replace(spec, spot=value)
    return replace(spec, volatility=value)
