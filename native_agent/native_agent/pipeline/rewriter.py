from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..providers.base import LLMProvider, GenerationConfig


BASE_SYSTEM_PROMPT = (
    "You are an assistant that rewrites user text into natural, native English while preserving meaning."
    " You fix grammar, clarity, and tone according to the requested style."
    " Do not add new information. If text is already natural, return it with minimal edits."
)


STYLE_INSTRUCTIONS = {
    "professional": "Use a polished, formal tone. Be clear and concise.",
    "casual": "Use a friendly, conversational tone without slang.",
    "concise": "Be brief and to the point. Remove unnecessary words.",
    "friendly": "Be warm and encouraging while remaining professional.",
}


@dataclass
class RewriteRequest:
    text: str
    style: str = "professional"
    extra_instructions: Optional[str] = None


class MessageRewriter:
    def __init__(self, provider: LLMProvider, model: str = "gpt-4o-mini"):
        self._provider = provider
        self._model = model

    def rewrite(self, request: RewriteRequest) -> str:
        style_instruction = STYLE_INSTRUCTIONS.get(request.style.lower(), STYLE_INSTRUCTIONS["professional"]) \
            + (f" {request.extra_instructions}" if request.extra_instructions else "")

        system_prompt = f"{BASE_SYSTEM_PROMPT} Style: {style_instruction}"

        user_prompt = (
            "Rewrite the following text. Output only the rewritten text, no explanations.\n\n"
            f"Text: {request.text}"
        )

        return self._provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            config=GenerationConfig(model=self._model, temperature=0.2, max_tokens=300),
        )

