from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OptionType = Literal["call", "put"]


@dataclass(frozen=True, slots=True)
class OptionSpec:
    spot: float
    strike: float
    rate: float
    volatility: float
    maturity: float
    option_type: OptionType
    dividend_yield: float = 0.0
