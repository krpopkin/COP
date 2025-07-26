import reflex as rx 
from db import get_user

class State(rx.State):
    """The app state."""
    userid: str = ""
    password: str = ""
    permission: str = ""
    login_error: str = ""

    def on_login(self):
        user = get_user(self.userid, self.password)
        if user:
            self.permission = user[1]
            self.login_error = ""
            return rx.redirect("/pacer")  # or /admin if permission is admin
        else:
            self.login_error = "Invalid credentials"