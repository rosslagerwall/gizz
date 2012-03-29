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
            try:
                with open(self._path, 'r') as in_file:
                    self._username = in_file.readline().strip()
            except IOError as e:
                if e.errno == 2:
                    raise UnknownUserException()
                else:
                    raise

        return self._username


class Authorizer:

    def __init__(self, username_grabber, password_grabber):
        self._username_grabber = username_grabber
        self._password_grabber = password_grabber

    def get_username(self):
        return self._username_grabber.get_username()

    def get_password(self):
        return self._password_grabber.get_password()


class UnknownUserException(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return 'unknown user'


class ForkNeededException(Exception):

    def __init__(self):
        pass

    def __str__(self):
        return 'Fork needed but --no-fork option passed.'


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
        
        editor = os.environ['EDITOR'] if 'EDITOR' in os.environ else 'nano'
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
