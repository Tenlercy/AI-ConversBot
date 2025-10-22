from __future__ import annotations

import os
import sys
from typing import Optional

import typer
from dotenv import load_dotenv

from .providers.openai_provider import OpenAIProvider
from .pipeline.rewriter import MessageRewriter, RewriteRequest
from .pipeline.eth_analyzer import ETHPriceAnalyzer


app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.command()
def rewrite(
    text: str = typer.Argument(..., help="Text to rewrite"),
    style: str = typer.Option("professional", help="Style: professional, casual, concise, friendly"),
    extra_instructions: Optional[str] = typer.Option(None, help="Additional guidance"),
    model: Optional[str] = typer.Option(None, help="Model name override"),
):
    """Rewrite text into native English."""
    load_dotenv()
    provider = OpenAIProvider()
    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    rewriter = MessageRewriter(provider=provider, model=model_name)
    result = rewriter.rewrite(RewriteRequest(text=text, style=style, extra_instructions=extra_instructions))
    typer.echo(result)


@app.command(name="analyze-eth")
def analyze_eth(model: Optional[str] = typer.Option(None, help="Model name override")):
    """Analyse recent ETH price movements using live market data."""

    load_dotenv()
    provider = OpenAIProvider()
    model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    analyzer = ETHPriceAnalyzer(provider=provider, model=model_name)
    result = analyzer.analyze()

    metrics = result.metrics
    header = (
        f"Current price: ${metrics.current_price:,.2f}\n"
        f"1h change: {metrics.hourly_change_pct:+.2f}%\n"
        f"24h change: {metrics.daily_change_pct:+.2f}%\n"
        f"24h high: ${metrics.high_24h:,.2f}\n"
        f"24h low: ${metrics.low_24h:,.2f}\n"
    )

    typer.echo(header)
    typer.echo("Analysis:\n" + result.summary)


def main():
    app()


if __name__ == "__main__":
    main()

