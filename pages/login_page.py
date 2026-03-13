from playwright.sync_api import Page, expect
from utils.config import BASE_URL, DEFAULT_TIMEOUT_MS


class LoginPage:
    """Page Object for SauceDemo login screen."""

    def __init__(self, page: Page):
        """Create page locators once to reuse them across tests."""
        self.page = page
        self.username_input = page.locator("//input[@id='user-name']")
        self.password_input = page.locator("//input[@id='password']")
        self.login_button = page.locator("//input[@id='login-button']")
        self.error_message = page.locator("//h3[@data-test='error']")

    def goto(self):
        """Open login URL and configure a default timeout for interactions."""
        self.page.goto(BASE_URL)
        self.page.set_default_timeout(DEFAULT_TIMEOUT_MS)

    def login(self, username: str, password: str):
        """Perform login using raw credentials."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def login_as(self, user: dict) -> None:
        """Perform login using a user dictionary with username/password keys."""
        self.login(user["username"], user["password"])

    def assert_login_loaded(self) -> None:
        """Assert that the browser is still on the login screen."""
        expect(self.page).to_have_url(BASE_URL)
        expect(self.page).to_have_title("Swag Labs")

    def assert_inventory_loaded(self) -> None:
        """Assert successful authentication redirect to inventory page."""
        expect(self.page).to_have_url(f"{BASE_URL}inventory.html")
        expect(self.page).to_have_title("Swag Labs")

    def assert_error_contains(self, message: str) -> None:
        """Assert that the visible login error message includes expected text."""
        expect(self.error_message).to_contain_text(message)