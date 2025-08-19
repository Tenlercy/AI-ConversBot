from __future__ import annotations

import os
import pytest

from native_agent.pipeline.rewriter import MessageRewriter, RewriteRequest
from native_agent.providers.base import LLMProvider, GenerationConfig


class DummyProvider(LLMProvider):
    def generate(self, system_prompt: str, user_prompt: str, *, config: GenerationConfig) -> str:
        # naive transformation to simulate improvements
        text = user_prompt.split("Text:", 1)[1].strip()
        return text.replace("wanna", "want to").replace("gonna", "going to")


def test_rewrite_basic():
    rewriter = MessageRewriter(provider=DummyProvider(), model="dummy")
    result = rewriter.rewrite(RewriteRequest(text="I wanna build up an AI agent", style="professional"))
    assert "want to" in result

