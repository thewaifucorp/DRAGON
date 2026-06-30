from dragon.adapters.base import GuardrailAdapter
from dragon.adapters.null import NullAdapter

_REGISTRY: dict[str, type[GuardrailAdapter]] = {
    "null": NullAdapter,
}
_plugins_loaded = False


def _load_plugins() -> None:
    global _plugins_loaded
    if _plugins_loaded:
        return
    _plugins_loaded = True
    from importlib.metadata import entry_points
    for ep in entry_points(group="dragon.adapters"):
        cls = ep.load()
        register(ep.name, cls)


def get_adapter(name: str) -> GuardrailAdapter:
    _load_plugins()
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(_REGISTRY)
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return cls()


def register(name: str, cls: type[GuardrailAdapter]) -> None:
    _REGISTRY[name] = cls
