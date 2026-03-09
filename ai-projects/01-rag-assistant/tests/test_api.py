from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_health():
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json()['ok'] is True


def test_ask_request_validation():
    res = client.post('/ask', json={'question': 'ok', 'k': 100})
    assert res.status_code == 422
