from fastapi.testclient import TestClient

import api


client = TestClient(api.app)


def test_health():
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json()['ok'] is True


def test_ask_request_validation():
    res = client.post('/ask', json={'question': 'ok', 'k': 100})
    assert res.status_code == 422


def test_auth_when_token_enabled():
    old_token = api.settings.api_token
    object.__setattr__(api.settings, "api_token", "secret")
    try:
        res = client.post('/ask', json={'question': 'what is rag?'})
        assert res.status_code == 401
        res_ok = client.post(
            '/ask',
            json={'question': 'what is rag?'},
            headers={'Authorization': 'Bearer secret'},
        )
        assert res_ok.status_code in (200, 422)
    finally:
        object.__setattr__(api.settings, "api_token", old_token)
