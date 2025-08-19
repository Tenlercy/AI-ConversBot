from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from ..providers.openai_provider import OpenAIProvider
from ..pipeline.rewriter import MessageRewriter, RewriteRequest


load_dotenv()

app = FastAPI(title="Native Agent API", version="0.1.0")


class RewriteBody(BaseModel):
    text: str = Field(..., description="Input text to rewrite")
    style: str = Field("professional", description="Desired style")
    extra_instructions: Optional[str] = Field(None, description="Additional guidance")
    model: Optional[str] = Field(None, description="Override model name")


def _get_rewriter(model_override: Optional[str] = None) -> MessageRewriter:
    provider = OpenAIProvider()
    model = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    return MessageRewriter(provider=provider, model=model)


@app.post("/rewrite")
def rewrite(body: RewriteBody):
    rewriter = _get_rewriter(model_override=body.model)
    result = rewriter.rewrite(
        RewriteRequest(text=body.text, style=body.style, extra_instructions=body.extra_instructions)
    )
    return {"result": result}


@app.get("/health")
def health():
    return {"ok": True}

