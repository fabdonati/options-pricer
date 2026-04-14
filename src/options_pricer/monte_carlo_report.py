from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from options_pricer.black_scholes import black_scholes_price
from options_pricer.models import OptionSpec
from options_pricer.monte_carlo import MonteCarloEstimate, monte_carlo_estimate


@dataclass(frozen=True, slots=True)
class MonteCarloReportRow:
    paths: int
    seed: int
    monte_carlo_price: float
    black_scholes_price: float
    abs_error_vs_black_scholes: float
    sample_variance: float
    standard_error: float
    ci_lower_95: float
    ci_upper_95: float


@dataclass(frozen=True, slots=True)
class MonteCarloReport:
    spec: OptionSpec
    path_counts: tuple[int, ...]
    rows: tuple[MonteCarloReportRow, ...]


def build_monte_carlo_report(
    spec: OptionSpec,
    *,
    path_counts: list[int],
    seed: int = 42,
) -> MonteCarloReport:
    if not path_counts:
        raise ValueError("path_counts must not be empty")
    if any(path_count <= 1 for path_count in path_counts):
        raise ValueError("each path count must be greater than 1")

    benchmark = black_scholes_price(spec)
    rows: list[MonteCarloReportRow] = []
    for path_count in path_counts:
        estimate = monte_carlo_estimate(spec, paths=path_count, seed=seed)
        rows.append(_row_from_estimate(estimate, benchmark=benchmark))

    return MonteCarloReport(
        spec=spec,
        path_counts=tuple(path_counts),
        rows=tuple(rows),
    )


def render_monte_carlo_report(report: MonteCarloReport) -> str:
    lines = [
        "Monte Carlo Diagnostics",
        f"Spot: {report.spec.spot:.6f}",
        f"Strike: {report.spec.strike:.6f}",
        f"Rate: {report.spec.rate:.6f}",
        f"Dividend yield: {report.spec.dividend_yield:.6f}",
        f"Volatility: {report.spec.volatility:.6f}",
        f"Maturity: {report.spec.maturity:.6f}",
        f"Type: {report.spec.option_type}",
        f"Path counts: {', '.join(str(path_count) for path_count in report.path_counts)}",
        "",
        (
            "Paths      Monte Carlo   Black-Scholes   Abs Error    Std Error    "
            "CI Lower     CI Upper"
        ),
    ]

    for row in report.rows:
        lines.append(
            f"{row.paths:<10d}"
            f"{row.monte_carlo_price:>13.6f}"
            f"{row.black_scholes_price:>17.6f}"
            f"{row.abs_error_vs_black_scholes:>12.6f}"
            f"{row.standard_error:>13.6f}"
            f"{row.ci_lower_95:>13.6f}"
            f"{row.ci_upper_95:>13.6f}"
        )

    return "\n".join(lines)


def write_monte_carlo_report_csv(report: MonteCarloReport, destination: str | Path) -> None:
    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "paths",
                "seed",
                "monte_carlo_price",
                "black_scholes_price",
                "abs_error_vs_black_scholes",
                "sample_variance",
                "standard_error",
                "ci_lower_95",
                "ci_upper_95",
            ]
        )
        for row in report.rows:
            writer.writerow(
                [
                    row.paths,
                    row.seed,
                    row.monte_carlo_price,
                    row.black_scholes_price,
                    row.abs_error_vs_black_scholes,
                    row.sample_variance,
                    row.standard_error,
                    row.ci_lower_95,
                    row.ci_upper_95,
                ]
            )


def write_monte_carlo_report_chart(report: MonteCarloReport, destination: str | Path) -> None:
    output_path = Path(destination)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_build_svg_chart(report), encoding="utf-8")


def _row_from_estimate(
    estimate: MonteCarloEstimate,
    *,
    benchmark: float,
) -> MonteCarloReportRow:
    return MonteCarloReportRow(
        paths=estimate.paths,
        seed=estimate.seed,
        monte_carlo_price=estimate.price,
        black_scholes_price=benchmark,
        abs_error_vs_black_scholes=abs(estimate.price - benchmark),
        sample_variance=estimate.sample_variance,
        standard_error=estimate.standard_error,
        ci_lower_95=estimate.ci_lower_95,
        ci_upper_95=estimate.ci_upper_95,
    )


def _build_svg_chart(report: MonteCarloReport) -> str:
    width = 920.0
    height = 560.0
    left_margin = 90.0
    right_margin = 40.0
    top_margin = 40.0
    bottom_margin = 70.0
    plot_width = width - left_margin - right_margin
    plot_height = height - top_margin - bottom_margin
    rows = list(report.rows)

    min_paths = min(row.paths for row in rows)
    max_paths = max(row.paths for row in rows)
    min_y = min(min(row.ci_lower_95, row.black_scholes_price) for row in rows)
    max_y = max(max(row.ci_upper_95, row.black_scholes_price) for row in rows)

    # Pad the y-axis so the band does not hug the border.
    y_padding = max(0.05, (max_y - min_y) * 0.1)
    min_y -= y_padding
    max_y += y_padding

    def x_scale(paths: int) -> float:
        if max_paths == min_paths:
            return left_margin + plot_width / 2.0
        return left_margin + ((paths - min_paths) / (max_paths - min_paths)) * plot_width

    def y_scale(value: float) -> float:
        if max_y == min_y:
            return top_margin + plot_height / 2.0
        return top_margin + (1.0 - ((value - min_y) / (max_y - min_y))) * plot_height

    estimate_points = " ".join(
        f"{x_scale(row.paths):.2f},{y_scale(row.monte_carlo_price):.2f}" for row in rows
    )
    ci_band_points = " ".join(
        f"{x_scale(row.paths):.2f},{y_scale(row.ci_upper_95):.2f}" for row in rows
    ) + " " + " ".join(
        f"{x_scale(row.paths):.2f},{y_scale(row.ci_lower_95):.2f}" for row in reversed(rows)
    )
    benchmark_y = y_scale(rows[0].black_scholes_price)

    x_ticks = rows
    y_ticks = [min_y + index * (max_y - min_y) / 4.0 for index in range(5)]

    svg_lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" '
            f'height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">'
        ),
        '<rect width="100%" height="100%" fill="#fbfaf6" />',
        (
            f'<text x="{left_margin}" y="24" font-size="22" '
            'font-family="Georgia, serif" fill="#1d2433">'
            "Monte Carlo convergence diagnostics</text>"
        ),
        (
            f'<text x="{left_margin}" y="46" font-size="12" '
            'font-family="Menlo, monospace" fill="#586070">'
            "Paths vs estimate with 95% confidence interval</text>"
        ),
        (
            f'<line x1="{left_margin}" y1="{top_margin}" '
            f'x2="{left_margin}" y2="{top_margin + plot_height}" '
            'stroke="#374151" stroke-width="1.5" />'
        ),
        (
            f'<line x1="{left_margin}" y1="{top_margin + plot_height}" '
            f'x2="{left_margin + plot_width}" y2="{top_margin + plot_height}" '
            'stroke="#374151" stroke-width="1.5" />'
        ),
        f'<polygon points="{ci_band_points}" fill="#cbd5e1" fill-opacity="0.55" stroke="none" />',
        (
            f'<line x1="{left_margin}" y1="{benchmark_y:.2f}" '
            f'x2="{left_margin + plot_width}" y2="{benchmark_y:.2f}" '
            'stroke="#b45309" stroke-width="2" stroke-dasharray="8 5" />'
        ),
        f'<polyline points="{estimate_points}" fill="none" stroke="#0f766e" stroke-width="3" />',
    ]

    for row in rows:
        x_value = x_scale(row.paths)
        y_value = y_scale(row.monte_carlo_price)
        svg_lines.append(
            f'<circle cx="{x_value:.2f}" cy="{y_value:.2f}" r="4.5" fill="#0f766e" />'
        )

    for tick in x_ticks:
        x_value = x_scale(tick.paths)
        svg_lines.extend(
            [
                (
                    f'<line x1="{x_value:.2f}" y1="{top_margin + plot_height}" '
                    f'x2="{x_value:.2f}" y2="{top_margin + plot_height + 6}" '
                    'stroke="#374151" stroke-width="1" />'
                ),
                (
                    f'<text x="{x_value:.2f}" y="{top_margin + plot_height + 24}" '
                    'text-anchor="middle" font-size="12" '
                    'font-family="Menlo, monospace" fill="#374151">'
                    f"{tick.paths}</text>"
                ),
            ]
        )

    for y_tick in y_ticks:
        y_value = y_scale(y_tick)
        svg_lines.extend(
            [
                (
                    f'<line x1="{left_margin - 6}" y1="{y_value:.2f}" '
                    f'x2="{left_margin}" y2="{y_value:.2f}" '
                    'stroke="#374151" stroke-width="1" />'
                ),
                (
                    f'<line x1="{left_margin}" y1="{y_value:.2f}" '
                    f'x2="{left_margin + plot_width}" y2="{y_value:.2f}" '
                    'stroke="#e5e7eb" stroke-width="1" />'
                ),
                (
                    f'<text x="{left_margin - 10}" y="{y_value + 4:.2f}" '
                    'text-anchor="end" font-size="12" '
                    'font-family="Menlo, monospace" fill="#374151">'
                    f"{y_tick:.2f}</text>"
                ),
            ]
        )

    legend_y = height - 24.0
    svg_lines.extend(
        [
            (
                f'<text x="{left_margin}" y="{legend_y}" font-size="12" '
                'font-family="Menlo, monospace" fill="#0f766e">'
                "Monte Carlo estimate</text>"
            ),
            (
                f'<text x="{left_margin + 180}" y="{legend_y}" font-size="12" '
                'font-family="Menlo, monospace" fill="#64748b">'
                "95% confidence band</text>"
            ),
            (
                f'<text x="{left_margin + 380}" y="{legend_y}" font-size="12" '
                'font-family="Menlo, monospace" fill="#b45309">'
                "Black-Scholes benchmark</text>"
            ),
            (
                f'<text x="{left_margin + plot_width - 2}" y="{legend_y}" '
                'text-anchor="end" font-size="12" '
                'font-family="Menlo, monospace" fill="#586070">'
                f"Type={report.spec.option_type}  "
                f"Vol={report.spec.volatility:.2f}  "
                f"T={report.spec.maturity:.2f}</text>"
            ),
            "</svg>",
        ]
    )
    return "\n".join(svg_lines)
