from unittest import mock

import pytest
from app import db
from app.auth.jwt import get_current_user
from app.feedback.schema import DisplayFeedback, Feedback
from app.user.schema import User
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.orm import Session

client = TestClient(app)

sample_user = User(
    id=1,
    username="testuser",
    email="testuser@example.com",
    name="Test User",
    password="password",
)
sample_feedback = Feedback(
    feedback="Great service!",
    image_file_name="testimage.jpg",
    predicted_class="dog",
    score=0.95,
)


@pytest.fixture
def mock_db_session():
    return mock.create_autospec(Session, instance=True)


@pytest.fixture
def mock_get_current_user():
    return sample_user


@mock.patch("app.feedback.router.services.new_feedback")
def test_create_feedback(mock_new_feedback, mock_db_session, mock_get_current_user):
    mock_new_feedback.return_value = sample_feedback

    payload = {
        "feedback": "Great service!",
        "image_file_name": "testimage.jpg",
        "predicted_class": "dog",
        "score": 0.95,
    }

    app.dependency_overrides[db.get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_get_current_user

    response = client.post(
        "/feedback/",
        json=payload,
    )

    assert response.status_code == 201

    args, kwargs = mock_new_feedback.call_args
    assert args[0].dict() == payload 
    assert args[1] == sample_user
    assert args[2] == mock_db_session


@mock.patch("app.feedback.router.services.all_feedback")
def test_get_all_feedback(mock_all_feedback, mock_db_session, mock_get_current_user):
    # Setup the mock service to return a list of feedback
    mock_all_feedback.return_value = [
        DisplayFeedback(
            id=1,
            feedback="Great service!",
            score=0.95,
            predicted_class="dog",
            image_file_name="testimage.jpg",
        )
    ]

    app.dependency_overrides[db.get_db] = lambda: mock_db_session
    app.dependency_overrides[get_current_user] = lambda: mock_get_current_user
    response = client.get(
        "/feedback/",
    )

    assert response.status_code == 200

    mock_all_feedback.assert_called_once_with(mock_db_session, sample_user)
