import pytest

from app.validators import ValidationError, validate_email, validate_username


class TestEmail:
    @pytest.mark.parametrize(
        "value",
        [
            "user@example.com",
            "first.last@sub.example.co",
            "u+tag@example.io",
            "USER@EXAMPLE.COM",
        ],
    )
    def test_valid(self, value):
        assert validate_email(value) == value.lower().strip()

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "no-at-sign",
            "a@b",
            "a@b.c",
            "user @example.com",
            "user@.com",
            "user@example.",
            "a" * 250 + "@example.com",
            123,
            None,
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            validate_email(value)


class TestUsername:
    @pytest.mark.parametrize("value", ["alice", "Bob_42", "user-name", "abc"])
    def test_valid(self, value):
        assert validate_username(value) == value

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "ab",
            "1user",
            "_user",
            "-user",
            "user!",
            "user name",
            "a" * 33,
            "us--er",
            "us__er",
            "us-_er",
            123,
            None,
        ],
    )
    def test_invalid(self, value):
        with pytest.raises(ValidationError):
            validate_username(value)
