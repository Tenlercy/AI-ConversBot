from __future__ import annotations

import os
import sys
from typing import Optional

import typer
from dotenv import load_dotenv

from .providers.openai_provider import OpenAIProvider
from .pipeline.rewriter import MessageRewriter, RewriteRequest


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


def main():
    app()


if __name__ == "__main__":
    main()

