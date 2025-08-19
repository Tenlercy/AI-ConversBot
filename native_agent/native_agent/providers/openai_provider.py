from __future__ import annotations

import os
from typing import Optional

from openai import OpenAI

from .base import LLMProvider, GenerationConfig


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, organization: Optional[str] = None):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = OpenAI(api_key=api_key, organization=organization)

    def generate(self, system_prompt: str, user_prompt: str, *, config: GenerationConfig) -> str:
        response = self._client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
        return response.choices[0].message.content or ""

