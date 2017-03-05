# Copyright 2012 Ross Lagerwall
# This file is part of gizz.

# gizz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# gizz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with gizz.  If not, see <http://www.gnu.org/licenses/>.

import getpass
import os
import subprocess
import tempfile
import filecmp
import shutil

_auth = None

def set_auth(auth):
    global _auth
    _auth = auth

def get_auth():
    return _auth

class AuthTokenAuthorizer:

    def __init__(self):
        self._username = None
        self._auth_token = None

    def get_username(self):
        if self._username is None:

            try:
                self._username = git_system('config', 'gizz.username').strip()
            except subprocess.CalledProcessError as e:
                raise UnknownUserException()

        return self._username

    def get_auth_token(self):
        if self._auth_token is None:

            try:
                self._auth_token = git_system('config', 'gizz.authtoken').strip()
            except subprocess.CalledProcessError as e:
                raise NoAuthTokenException()

        return self._auth_token


class UnknownUserException(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return 'unknown user'


class NoAuthTokenException(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return 'no auth token'


class ForkNeededException(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return 'Fork needed but --no-fork option passed.'


class InvalidArgumentException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Invalid argument: ' + self.msg


class InvalidRepositoryException(Exception):

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Invalid repository: ' + self.msg


class MessageGetter:

    def __init__(self):
        self._f = tempfile.NamedTemporaryFile(mode='w', delete=False)
        self._f.write("\n/// ALL LINES BELOW ARE IGNORED\n\n")

    def add_line(self, line):
        self._f.write(line + "\n")

    def _parse(self, s):
        s = s.split("/// ALL LINES BELOW ARE IGNORED")
        if len(s) == 1:
            return s
        else:
            return s[0].strip() + "\n"

    def edit(self):
        self._f.close()
        f, copy_name = tempfile.mkstemp()
        os.close(f)
        shutil.copy(self._f.name, copy_name)

        editor = os.environ['EDITOR'] if 'EDITOR' in os.environ else 'vi'
        with subprocess.Popen([editor, self._f.name]) as p:
            p.wait()

        no_diff = filecmp.cmp(self._f.name, copy_name)

        with open(self._f.name, 'r') as f:
            result = f.read()

        os.unlink(self._f.name)
        os.unlink(copy_name)

        return None if no_diff else self._parse(result)


class TitledMessageGetter(MessageGetter):

    def __init__(self):
        MessageGetter.__init__(self)
        self._f.write("/// FIRST LINE SHOULD CONTAIN THE TITLE\n")
        self._f.write("/// SUBSEQUENT LINES SHOULD CONTAIN THE BODY\n\n")

    def _parse(self, s):
        s = MessageGetter._parse(self, s)
        s = s.split("\n")
        title = s[0].strip()
        body = "\n".join(s[1:]).strip()
        body += '' if body == '' else "\n"
        return title, body


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

# Returns ~/.config/gizz/config in the usual case
def get_config_path():
    config_home = os.getenv('XDG_CONFIG_HOME')
    if config_home is None:
        config_home = os.path.expanduser('~/.config')

    config_dir = os.path.join(config_home, 'gizz')
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, 'config')
