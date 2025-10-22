"""Ethereum price analysis pipeline components."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Optional, Protocol, Sequence

import httpx

from ..providers.base import GenerationConfig, LLMProvider


@dataclass(frozen=True)
class PricePoint:
    """Represents a single ETH price observation."""

    timestamp: datetime
    price: float


class ETHMarketDataSource(Protocol):
    """Protocol for objects capable of returning ETH market data."""

    def fetch_price_points(self) -> Sequence[PricePoint]:
        """Return a chronologically ordered sequence of price points."""
        raise NotImplementedError


class CoinGeckoETHDataSource:
    """Fetches ETH market data from the public CoinGecko API."""

    def __init__(
        self,
        *,
        requester: Callable[..., httpx.Response] | None = None,
        days: float = 1.0,
        interval: str = "hourly",
        base_url: str = "https://api.coingecko.com/api/v3",
        timeout: float = 10.0,
    ) -> None:
        self._requester = requester or httpx.get
        self._days = days
        self._interval = interval
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def fetch_price_points(self) -> Sequence[PricePoint]:
        url = f"{self._base_url}/coins/ethereum/market_chart"
        response = self._requester(
            url,
            params={
                "vs_currency": "usd",
                "days": self._days,
                "interval": self._interval,
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        prices: Iterable[List[float]] = payload.get("prices", [])  # type: ignore[assignment]

        points: List[PricePoint] = []
        for entry in prices:
            if len(entry) < 2:
                continue
            timestamp_ms, price = entry[0], entry[1]
            # CoinGecko returns timestamps in milliseconds.
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            points.append(PricePoint(timestamp=timestamp, price=float(price)))

        if len(points) < 2:
            raise RuntimeError("Not enough price points returned from CoinGecko")

        return points


@dataclass(frozen=True)
class ETHPriceMetrics:
    current_price: float
    hourly_change_pct: float
    daily_change_pct: float
    high_24h: float
    low_24h: float


@dataclass(frozen=True)
class ETHAnalysisResult:
    metrics: ETHPriceMetrics
    summary: str


class ETHPriceAnalyzer:
    """Use market data and an LLM to analyse ETH price movements."""

    def __init__(
        self,
        provider: LLMProvider,
        *,
        model: str = "gpt-4o-mini",
        data_source: Optional[ETHMarketDataSource] = None,
    ) -> None:
        self._provider = provider
        self._model = model
        self._data_source = data_source or CoinGeckoETHDataSource()

    def analyze(self) -> ETHAnalysisResult:
        points = list(self._data_source.fetch_price_points())
        if len(points) < 2:
            raise RuntimeError("At least two price points are required for analysis")

        current = points[-1].price
        previous = points[-2].price
        first = points[0].price

        hourly_change_pct = self._calculate_change(previous, current)
        daily_change_pct = self._calculate_change(first, current)
        high = max(p.price for p in points)
        low = min(p.price for p in points)

        metrics = ETHPriceMetrics(
            current_price=current,
            hourly_change_pct=hourly_change_pct,
            daily_change_pct=daily_change_pct,
            high_24h=high,
            low_24h=low,
        )

        summary = self._generate_summary(metrics, recent_points=points[-6:])
        return ETHAnalysisResult(metrics=metrics, summary=summary)

    def _generate_summary(self, metrics: ETHPriceMetrics, *, recent_points: Sequence[PricePoint]) -> str:
        price_lines = "\n".join(
            f"- {point.timestamp.isoformat()} UTC: ${point.price:,.2f}" for point in recent_points
        )

        system_prompt = (
            "You are a cryptocurrency market analyst focusing on Ethereum (ETH)."
            " Analyse short-term momentum, key levels, and potential catalysts without giving investment advice."
        )
        user_prompt = (
            "Provide a concise analysis of ETH price action based on the following metrics and recent prices.\n"
            f"Current price: ${metrics.current_price:,.2f}\n"
            f"1h change: {metrics.hourly_change_pct:+.2f}%\n"
            f"24h change: {metrics.daily_change_pct:+.2f}%\n"
            f"24h high: ${metrics.high_24h:,.2f}\n"
            f"24h low: ${metrics.low_24h:,.2f}\n"
            "Recent prices:\n"
            f"{price_lines}\n"
            "Explain momentum, volatility, and notable support/resistance zones."
        )

        return self._provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            config=GenerationConfig(model=self._model, temperature=0.3, max_tokens=400),
        )

    @staticmethod
    def _calculate_change(old_price: float, new_price: float) -> float:
        if old_price == 0:
            return 0.0
        return (new_price - old_price) / old_price * 100
