
from pi_ai.env_keys import get_env_api_key


class TestEnvKeys:
    def test_get_env_api_key_existing(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")

        result = get_env_api_key("openai")
        assert result == "test-openai-key"

    def test_get_env_api_key_anthropic(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")

        result = get_env_api_key("anthropic")
        assert result == "test-anthropic-key"

    def test_get_env_api_key_google(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")

        result = get_env_api_key("google")
        assert result == "test-gemini-key"

    def test_get_env_api_key_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        result = get_env_api_key("openai")
        assert result is None

    def test_get_env_api_key_unknown_provider(self):
        result = get_env_api_key("unknown-provider")
        assert result is None
