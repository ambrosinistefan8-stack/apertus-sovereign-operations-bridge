import json
import unittest
from unittest.mock import patch

from app.apertus_client import OpenAICompatibleApertusClient


class _FakeResponse:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self._body


class ApertusClientTests(unittest.TestCase):
    def _payload(self, content):
        return {"choices": [{"message": {"content": content}}]}

    def test_live_client_uses_openai_compatible_chat_endpoint(self):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["authorization"] = request.get_header("Authorization")
            captured["timeout"] = timeout
            captured["body"] = json.loads(request.data.decode("utf-8"))
            content = json.dumps(
                {
                    "facts": [
                        {
                            "key": "product",
                            "value": "Apertus Office Pack",
                            "source_id": "product",
                            "confidence": 1.0,
                        }
                    ],
                    "missing_required": [],
                    "untrusted_instructions": [],
                    "proposed_response": "Draft ready.",
                    "requested_actions": ["draft_response"],
                }
            )
            return _FakeResponse(self._payload(content))

        client = OpenAICompatibleApertusClient(
            base_url="https://example.invalid/v1/",
            api_key="test-secret",
            model="swiss-ai/Apertus-v1.5-8B",
        )

        with patch("app.apertus_client.urllib.request.urlopen", side_effect=fake_urlopen):
            result = client.analyze("system", "user")

        self.assertEqual(captured["url"], "https://example.invalid/v1/chat/completions")
        self.assertEqual(captured["authorization"], "Bearer test-secret")
        self.assertEqual(captured["timeout"], 90)
        self.assertEqual(captured["body"]["model"], "swiss-ai/Apertus-v1.5-8B")
        self.assertEqual(result.facts[0].key, "product")

    def test_fenced_json_is_parsed(self):
        content = """```json
{"facts":[],"missing_required":[],"untrusted_instructions":[],"proposed_response":"ok","requested_actions":[]}
```"""
        parsed = OpenAICompatibleApertusClient._extract_json(content)
        self.assertEqual(parsed["proposed_response"], "ok")


if __name__ == "__main__":
    unittest.main()
