"""Tests for configuration defaults."""

import os


class TestSettingsDefaults:
    """Verify config defaults are sensible when no env vars are set."""

    def test_fmp_base_url(self):
        from config.settings import FMP_BASE_URL
        assert FMP_BASE_URL == "https://financialmodelingprep.com/stable"

    def test_default_collection_name(self):
        from config.settings import CHROMA_COLLECTION
        # Should have a default even without env var
        assert CHROMA_COLLECTION is not None
        assert isinstance(CHROMA_COLLECTION, str)

    def test_default_embedding_model(self):
        from config.settings import EMBEDDING_MODEL
        assert EMBEDDING_MODEL is not None
        assert "embedding" in EMBEDDING_MODEL

    def test_default_ingestor_url(self):
        from config.settings import INGESTOR_BASE_URL
        assert "localhost" in INGESTOR_BASE_URL or INGESTOR_BASE_URL.startswith("http")
