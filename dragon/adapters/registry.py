from dragon.adapters.base import GuardrailAdapter
from dragon.adapters.null import NullAdapter

_REGISTRY: dict[str, type[GuardrailAdapter]] = {
    "null": NullAdapter,
}


def get_adapter(name: str) -> GuardrailAdapter:
    """Resolve an adapter by name. Used by task files so Inspect CLI can pass --task-arg adapter=<name>."""
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(_REGISTRY)
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return cls()


def register(name: str, cls: type[GuardrailAdapter]) -> None:
    _REGISTRY[name] = cls
