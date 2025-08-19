from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class GenerationConfig:
    model: str
    temperature: float = 0.2
    max_tokens: Optional[int] = None


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, *, config: GenerationConfig) -> str:
        """Generate a single completion string."""
        raise NotImplementedError

