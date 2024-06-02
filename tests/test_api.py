import pytest
import requests

BASE_URL = "http://127.0.0.1:5000"


def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_update_context():
    data = {
        "file_path": "caminho/do/arquivo.py",
        "content": "Conteúdo do arquivo."
    }
    response = requests.post(f"{BASE_URL}/context", json=data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_get_context():
    file_path = "caminho/do/arquivo.py"
    response = requests.get(f"{BASE_URL}/context/{file_path}")
    assert response.status_code == 200
    assert "content" in response.json()


def test_delete_context():
    file_path = "caminho/do/arquivo.py"
    response = requests.delete(f"{BASE_URL}/context/{file_path}")
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_generate_response():
    data = {
        "prompt": "Explique o que faz este trecho de código."
    }
    response = requests.post(f"{BASE_URL}/generate-response", json=data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
