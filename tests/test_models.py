import pytest

# unit tests for the User model


def test_user_password_hashing_behaves_correctly():
    from models import User

    user = User(username="testuser")
    user.set_password("securepassword")
    assert user.check_password("securepassword") is True
    assert user.check_password("wrongpassword") is False


def test_password_hashing_is_unique():
    from models import User

    user1 = User(username="user1")
    user2 = User(username="user2")

    user1.set_password("samepassword")
    user2.set_password("samepassword")

    assert user1.password_hash != user2.password_hash


if __name__ == "__main__":
    pytest.main()
