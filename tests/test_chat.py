"""Tests for the chat API endpoint."""

import json
import os
import sys
from unittest.mock import patch, MagicMock

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api"))
import chat


@pytest.fixture
def client():
    chat.app.config["TESTING"] = True
    chat._rate_store.clear()
    with chat.app.test_client() as c:
        yield c


class TestChatEndpoint:
    def test_options_returns_204(self, client):
        resp = client.options("/api/chat")
        assert resp.status_code == 204

    @patch.object(chat, "client")
    def test_valid_message(self, mock_openai, client):
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello!"
        mock_openai.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        resp = client.post("/api/chat", json={"message": "Hi"})
        assert resp.status_code == 200
        assert json.loads(resp.data)["reply"] == "Hello!"

    def test_missing_message(self, client):
        resp = client.post("/api/chat", json={})
        assert resp.status_code == 400
        assert "Missing message" in json.loads(resp.data)["error"]

    def test_empty_message(self, client):
        resp = client.post("/api/chat", json={"message": "   "})
        assert resp.status_code == 400
        assert "Empty message" in json.loads(resp.data)["error"]

    def test_message_too_long(self, client):
        resp = client.post("/api/chat", json={"message": "x" * 1001})
        assert resp.status_code == 400
        assert "too long" in json.loads(resp.data)["error"]

    def test_non_string_message(self, client):
        resp = client.post("/api/chat", json={"message": 123})
        assert resp.status_code == 400

    def test_no_json_body(self, client):
        resp = client.post("/api/chat", data="not json", content_type="text/plain")
        assert resp.status_code == 400

    @patch.object(chat, "client")
    def test_openai_error_returns_502(self, mock_openai, client):
        mock_openai.chat.completions.create.side_effect = Exception("API down")
        resp = client.post("/api/chat", json={"message": "Hi"})
        assert resp.status_code == 502
        assert "wrong" in json.loads(resp.data)["error"].lower()


class TestRateLimiting:
    @patch.object(chat, "client")
    def test_rate_limit_triggered(self, mock_openai, client):
        mock_choice = MagicMock()
        mock_choice.message.content = "Hi"
        mock_openai.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

        for _ in range(chat.RATE_LIMIT):
            resp = client.post("/api/chat", json={"message": "Hi"})
            assert resp.status_code == 200

        resp = client.post("/api/chat", json={"message": "Hi"})
        assert resp.status_code == 429
        assert "Too many" in json.loads(resp.data)["error"]


class TestCORS:
    def test_cors_allowed_origin(self, client):
        resp = client.options("/api/chat", headers={"Origin": "https://aidoo.biz"})
        assert resp.headers.get("Access-Control-Allow-Origin") == "https://aidoo.biz"

    def test_cors_disallowed_origin(self, client):
        resp = client.options("/api/chat", headers={"Origin": "https://evil.com"})
        assert "Access-Control-Allow-Origin" not in resp.headers
