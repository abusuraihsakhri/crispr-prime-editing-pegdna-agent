"""
Deterministic mock response provider with outbound identifier checks.
"""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Crispr Prime Editing Pegdna Agent"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        excerpt = prompt[:80]
        return (
            f"[{self.system_name} mock responder] No external model was called. "
            "This endpoint does not validate scientific correctness. "
            f"Received: '{excerpt}...'"
        )


class LLMFactory:
    """Create the deterministic mock responder used by the current repository."""

    @staticmethod
    def create(
        provider: str = "mock",
        system_name: str = "Crispr Prime Editing Pegdna Agent",
    ):
        prov = str(provider).lower()
        if prov not in {"mock", "deterministic", "test"}:
            raise ValueError(
                f"Unsupported model provider {provider!r}; "
                "this repository currently implements only the mock provider."
            )
        return MockLLM(system_name)
