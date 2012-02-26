import getpass
import ghlib

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


class Authorizer:

    def __init__(self, username_grabber, password_grabber):
        self._username_grabber = username_grabber
        self._password_grabber = password_grabber

    def get_username(self):
        return self._username_grabber.get_username()

    def get_password(self):
        return self._password_grabber.get_password()


def do_list_repos(args):
    username = args.user
    user = ghlib.User(username)
    for repo in user.get_repo_list():
        print(repo.repo)

def do_list_branches(args):
    user_repo = args.user_repo
    user, repo = user_repo.split('/')
    repo = ghlib.Repository(user, repo)
    for branch in repo.get_branch_list():
        print(branch.name)

def do_fork(args):
    user_repo = args.user_repo
    user, reponame = user_repo.split('/')
    repo = ghlib.Repository(user, reponame)
    repo.auth = auth
    newrep = repo.fork()
    newrep.dump()

def do_list_pull_requests(args):
    user_repo = args.user_repo
    user, repo = user_repo.split('/')
    repo = ghlib.Repository(user, repo)
    for pr in repo.get_pull_request_list():
        print(pr.id, pr.title)

def do_fetch_pull_request(args):
    user_repo = args.user_repo
    user, repo = user_repo.split('/')
    id = args.id
    repo = ghlib.Repository(user, repo)
    pr = repo.get_pull_request(id)
    print(pr.id, pr.title)
    # git origin add user git_url
    # git fetch user
    # git branch branchname user/branch
