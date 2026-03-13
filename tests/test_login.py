"""Login end-to-end tests following Page Object Model conventions."""

import pytest

from data.users import INVALID_USER, LOCKED_USER, STANDARD_USER
from pages.login_page import LoginPage


def test_valid_login(page):
    """Validate that a standard user can access the inventory page."""
    login_page = LoginPage(page)

    login_page.goto()
    login_page.login_as(STANDARD_USER)

    login_page.assert_inventory_loaded()


@pytest.mark.parametrize(
    ("user_data", "expected_error"),
    [
        pytest.param(
            LOCKED_USER,
            "Epic sadface: Sorry, this user has been locked out.",
            id="locked_user_cannot_log_in",
        ),
        pytest.param(
            INVALID_USER,
            "Epic sadface: Username and password do not match any user in this service",
            id="invalid_credentials_show_error",
        ),
    ],
)
def test_login_error_messages_for_invalid_scenarios(page, user_data, expected_error):
    """Validate login error handling for locked and invalid users."""
    login_page = LoginPage(page)

    login_page.goto()
    login_page.login_as(user_data)

    login_page.assert_error_contains(expected_error)
