import reflex as rx 
from db import get_user, get_all_users, add_user, update_user_permission, delete_user

class State(rx.State):
    """The app state."""
    userid: str = ""
    password: str = ""
    permission: str = ""
    login_error: str = ""

    users: list[tuple[str, str]] = []  # List of (username, permission)

    new_username: str = ""
    new_password: str = ""
    new_permission: str = "browse"
    
    edit_permission: dict[str, str] = {}

    def on_login(self):
        user = get_user(self.userid, self.password)
        if user:
            self.permission = user[1]
            self.login_error = ""
            return rx.redirect("/pacer")  
        else:
            self.login_error = "Invalid credentials"
            
    def load_users(self):
        self.users = get_all_users()
        self.edit_permission = {user[0]: user[1] for user in self.users}

    def on_add_user(self):
        add_user(self.new_username, self.new_password, self.new_permission)
        self.new_username = ""
        self.new_password = ""
        self.new_permission = "browse"
        self.load_users()

    def on_update_permission(self, username: str, permission: str):
        self.edit_permission[username] = permission

    def on_save_permission(self, username: str):
        update_user_permission(username, self.edit_permission[username])
        self.load_users()

    def on_delete_user(self, username: str):
        delete_user(username)
        self.load_users()