from .mulerun import MuleRunProvider
from .apimart import ApimartProvider
from .atlascloud import AtlasCloudProvider

_PROVIDERS = {
    "mulerun": MuleRunProvider,
    "apimart": ApimartProvider,
    "atlascloud": AtlasCloudProvider,
}


def get_provider(name: str, api_key: str):
    """Return an instantiated provider by name."""
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name}")
    return cls(api_key)


def get_provider_class(name: str):
    """Return the provider class (for accessing class-level attributes like env_var)."""
    return _PROVIDERS[name]
