import json

from src.app import lambda_handler


def test_returns_200():
    response = lambda_handler({}, None)
    assert response["statusCode"] == 200


def test_body_contains_message():
    response = lambda_handler({}, None)
    body = json.loads(response["body"])
    assert "message" in body
