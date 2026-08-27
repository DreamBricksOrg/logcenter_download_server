import secrets
from functools import wraps

from flask import redirect, session, url_for

import config


def verify_credentials(username, password):
    valid_user = secrets.compare_digest(username or "", config.APP_USERNAME)
    valid_pass = secrets.compare_digest(password or "", config.APP_PASSWORD)
    return valid_user and valid_pass


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped
