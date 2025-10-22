from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence

import pytest

from native_agent.pipeline.eth_analyzer import (
    ETHPriceAnalyzer,
    PricePoint,
)
from native_agent.providers.base import GenerationConfig, LLMProvider


class StubDataSource:
    def __init__(self) -> None:
        base = datetime(2024, 1, 1, tzinfo=timezone.utc)
        self._points = [
            PricePoint(timestamp=base + timedelta(hours=i), price=1800.0 + i * 10.0) for i in range(25)
        ]

    def fetch_price_points(self) -> Sequence[PricePoint]:
        return self._points


class DummyProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = []

    def generate(self, system_prompt: str, user_prompt: str, *, config: GenerationConfig) -> str:
        self.calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "config": config,
        })
        return "ETH is showing steady upward momentum with modest volatility."


def test_eth_price_analyzer_returns_metrics_and_summary():
    analyzer = ETHPriceAnalyzer(provider=DummyProvider(), model="dummy", data_source=StubDataSource())
    result = analyzer.analyze()

    assert result.metrics.current_price == pytest.approx(2040.0)
    assert result.metrics.high_24h == pytest.approx(2040.0)
    assert result.metrics.low_24h == pytest.approx(1800.0)
    assert result.metrics.hourly_change_pct == pytest.approx(0.4926, rel=1e-3)
    assert result.metrics.daily_change_pct == pytest.approx(13.3333, rel=1e-3)
    assert "upward momentum" in result.summary.lower()


def test_generate_summary_uses_recent_points():
    provider = DummyProvider()
    analyzer = ETHPriceAnalyzer(provider=provider, model="dummy", data_source=StubDataSource())
    analyzer.analyze()

    assert provider.calls, "Provider should have been invoked"
    call = provider.calls[0]
    assert "You are a cryptocurrency market analyst" in call["system_prompt"]
    assert "Current price: $2,040.00" in call["user_prompt"]
    assert call["config"].model == "dummy"
    # Ensure the user prompt references ISO formatted timestamps from the recent window
    assert call["user_prompt"].count("UTC") >= 1
