import getpass
import os
import subprocess

class PasswordGrabber:

    def __init__(self):
        self._password = None

    def get_password(self):
        if self._password is None:
            self._get_password_from_user()

        return self._password


class BasicPasswordGrabber(PasswordGrabber):

    def _get_password_from_user(self):
        self._password = getpass.getpass()


class BasicUsernameGrabber:

    def __init__(self, username):
        self._username = username

    def get_username(self):
        return self._username


class StoredUsernameGrabber:

    def __init__(self):
        self._username = None
        self._path = os.path.expanduser('~/.gizzconfig')

    def get_username(self):
        if self._username is None:
            with open(self._path, 'r') as in_file:
                self._username = in_file.readline().strip()

        return self._username


class Authorizer:

    def __init__(self, username_grabber, password_grabber):
        self._username_grabber = username_grabber
        self._password_grabber = password_grabber

    def get_username(self):
        return self._username_grabber.get_username()

    def get_password(self):
        return self._password_grabber.get_password()


def git_system(*args):
    cmdline = ['git']
    cmdline.extend(args)
    with open(os.devnull, 'wb') as null:
        return subprocess.check_output(cmdline, stderr=null).decode()

def git_run(*args):
    cmdline = ['git']
    cmdline.extend(args)
    with open(os.devnull, 'wb') as null:
        subprocess.check_call(cmdline, stdout=null, stderr=null)
