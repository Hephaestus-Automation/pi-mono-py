
from pi_ai.registry import (
    clear_api_providers,
    get_api_provider,
    get_api_providers,
    register_api_provider,
    unregister_api_providers,
)


class MockApiProvider:
    def __init__(self, api: str, name: str):
        self.api = api
        self.name = name


class TestRegistry:
    def test_register_and_get_provider(self):
        provider = MockApiProvider("test-api", "Test Provider")

        register_api_provider(provider, source_id="test-source")

        retrieved = get_api_provider("test-api")
        assert retrieved is not None
        assert retrieved.name == "Test Provider"

    def test_get_nonexistent_provider(self):
        result = get_api_provider("nonexistent-api")
        assert result is None

    def test_get_all_providers(self):
        provider1 = MockApiProvider("api1", "Provider 1")
        provider2 = MockApiProvider("api2", "Provider 2")

        register_api_provider(provider1, source_id="source1")
        register_api_provider(provider2, source_id="source2")

        providers = get_api_providers()
        assert len(providers) >= 2

        names = [p.name for p in providers]
        assert "Provider 1" in names
        assert "Provider 2" in names

    def test_unregister_by_source(self):
        provider = MockApiProvider("api-to-remove", "To Remove")

        register_api_provider(provider, source_id="remove-source")

        retrieved = get_api_provider("api-to-remove")
        assert retrieved is not None

        unregister_api_providers("remove-source")

        retrieved = get_api_provider("api-to-remove")
        assert retrieved is None

    def test_clear_all_providers(self):
        provider1 = MockApiProvider("clear-api-1", "Clear 1")
        provider2 = MockApiProvider("clear-api-2", "Clear 2")

        register_api_provider(provider1)
        register_api_provider(provider2)

        clear_api_providers()

        providers = get_api_providers()
        assert len(providers) == 0
