"""Ethereum price analysis pipeline components."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Iterable, List, Optional, Protocol, Sequence

try:  # pragma: no cover - optional dependency guard
    from openai import RateLimitError  # type: ignore
except Exception:  # pragma: no cover - we only need the type when available
    RateLimitError = None  # type: ignore[assignment]

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
        provider: Optional[LLMProvider],
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

        summary = self._build_summary(metrics, recent_points=points[-6:])
        return ETHAnalysisResult(metrics=metrics, summary=summary)

    def _build_summary(
        self,
        metrics: ETHPriceMetrics,
        *,
        recent_points: Sequence[PricePoint],
    ) -> str:
        if self._provider is None:
            return self._build_fallback_summary(
                metrics,
                recent_points=recent_points,
                reason="offline",
                error_message="LLM provider disabled",
            )

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

        try:
            return self._provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                config=GenerationConfig(model=self._model, temperature=0.3, max_tokens=400),
            )
        except Exception as exc:  # pragma: no cover - exercised in specific tests
            if self._is_rate_limit_error(exc):
                return self._build_fallback_summary(
                    metrics,
                    recent_points=recent_points,
                    reason="rate_limit",
                    error_message=str(exc),
                )
            raise

    @staticmethod
    def _calculate_change(old_price: float, new_price: float) -> float:
        if old_price == 0:
            return 0.0
        return (new_price - old_price) / old_price * 100

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        if RateLimitError is not None and isinstance(error, RateLimitError):
            return True
        status_code = getattr(error, "status_code", None)
        if status_code == 429:
            return True
        message = str(error).lower()
        return "insufficient_quota" in message or "rate limit" in message

    def _build_fallback_summary(
        self,
        metrics: ETHPriceMetrics,
        *,
        recent_points: Sequence[PricePoint],
        reason: str,
        error_message: str,
    ) -> str:
        direction_hour = "up" if metrics.hourly_change_pct >= 0 else "down"
        direction_day = "higher" if metrics.daily_change_pct >= 0 else "lower"
        hourly_pct = abs(metrics.hourly_change_pct)
        daily_pct = abs(metrics.daily_change_pct)
        range_width = metrics.high_24h - metrics.low_24h
        range_pct = (range_width / metrics.low_24h * 100) if metrics.low_24h else 0.0

        if reason == "offline":
            headline = "Offline summary enabled — no OpenAI calls were made."
        else:
            headline = (
                "⚠️ OpenAI quota or rate limit was reached. Showing a locally generated summary instead."
            )

        advisory = (
            "在 Google Colab 上如果看到 429 insufficient_quota，请确保你的 OpenAI 账户有额度"
            "，或者使用 `python -m native_agent.cli analyze-eth --offline` 运行纯本地模式。"
        )

        recent_section = "\n".join(
            f"- {point.timestamp.isoformat()} UTC: ${point.price:,.2f}" for point in recent_points
        )

        lines = [
            headline,
            advisory,
            "",
            "Key stats:",
            f"- Spot price: ${metrics.current_price:,.2f}",
            f"- 1h momentum: {direction_hour} {hourly_pct:.2f}%",
            f"- 24h trend: {direction_day} by {daily_pct:.2f}%",
            f"- Day range: ${metrics.low_24h:,.2f} → ${metrics.high_24h:,.2f} ({range_pct:.2f}% span)",
            "",
            "Recent datapoints:",
            recent_section,
        ]

        if error_message:
            lines.append("")
            lines.append(f"Debug: {error_message}")

        return "\n".join(lines)
