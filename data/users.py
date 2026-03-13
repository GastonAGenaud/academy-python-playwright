"""Reusable test users for SauceDemo authentication scenarios."""

# Happy-path credentials provided by SauceDemo.
STANDARD_USER = {
    "username": "standard_user",
    "password": "secret_sauce",
}

# Business rule scenario: user exists but is blocked.
LOCKED_USER = {
    "username": "locked_out_user",
    "password": "secret_sauce",
}

# Negative scenario: unknown user and invalid password.
INVALID_USER = {
    "username": "invalid_user",
    "password": "wrong_password",
}
