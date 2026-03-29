"""Tests for the enrichment module — chunk_text is pure logic, no external deps."""

from app.enrichment import chunk_text, CHUNK_SIZE


class TestChunkText:

    def test_short_text_single_chunk(self):
        text = "Hello world"
        chunks = chunk_text(text)
        assert chunks == ["Hello world"]

    def test_exact_chunk_size(self):
        text = "a" * CHUNK_SIZE
        chunks = chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_splits_long_text(self):
        text = "a" * (CHUNK_SIZE * 3 + 100)
        chunks = chunk_text(text)
        assert len(chunks) == 4
        assert "".join(chunks) == text

    def test_custom_chunk_size(self):
        text = "abcdefghij"  # 10 chars
        chunks = chunk_text(text, chunk_size=3)
        assert chunks == ["abc", "def", "ghi", "j"]

    def test_empty_text(self):
        chunks = chunk_text("")
        assert chunks == [""]

    def test_chunk_size_one(self):
        text = "abc"
        chunks = chunk_text(text, chunk_size=1)
        assert chunks == ["a", "b", "c"]

    def test_preserves_all_content(self):
        text = "The quick brown fox jumps over the lazy dog. " * 50
        chunks = chunk_text(text, chunk_size=100)
        reassembled = "".join(chunks)
        assert reassembled == text


class TestChunkSizeConstant:

    def test_default_chunk_size(self):
        assert CHUNK_SIZE == 500
