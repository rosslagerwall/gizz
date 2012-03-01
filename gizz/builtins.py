import os.path
import re
import gizz.ghlib
from gizz.utils import *

class Cmd:

    def __init__(self):
        pass

    def set_authorizer(self, auth):
        self._auth = auth

    def _get_gh_name(self, remote_name):
        output = git_system('remote', '-v', 'show')
        for line in output.strip().split('\n'):
            name, url, _ = line.split()
            if name == remote_name and 'github.com' in url:
                return re.findall('\w+/\w+\.git', url)[0][:-4].split('/')

        return (None, None)

    def _get_best_gh_name(self):
        user, repo = self._get_gh_name(self._auth.get_username())
        if user is None or repo is None:
            user, repo = self._get_gh_name('origin')
            if user is None or repo is None:
                # raise exception
                pass
        return user, repo


class Cmd_ListRepos(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._username = args.user

    def run(self):
        if self._username is None:
            user = gizz.ghlib.User(self._auth.get_username())
        else:
            user = gizz.ghlib.User(self._username)
        for repo in user.get_repo_list():
            print(repo.reponame)


class Cmd_ListBranches(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo

    def run(self):
        if self._arg_repo is None:
            user, repo = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        for branch in repo.get_branch_list():
            print(branch.name)


class Cmd_ListTags(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo

    def run(self):
        if self._arg_repo is None:
            user, repo = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        for tag in repo.get_tag_list():
            print(tag.name, tag.sha[:10])


class Cmd_Fork(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo

    def run(self):
        if self._arg_repo is None:
            user, repo = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        repo.auth = self._auth
        newrep = repo.fork()
        newrep.dump()


class Cmd_ListPullRequests(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo

    def run(self):
        if self._arg_repo is None:
            user, repo = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        for pr in repo.get_pull_request_list():
            print(pr.id, pr.title)


class Cmd_FetchPullRequest(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo
        self._id = args.id
        self._fetch_all = args.id is None

    def run(self):
        if self._arg_repo is None:
            user, repo = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        if self._fetch_all:
            for pr in repo.get_pull_request_list():
                self._fetch_one_pull_request(pr)
        else:
            pr = repo.get_pull_request(self._id)
            self._fetch_one_pull_request(pr)

    def _fetch_one_pull_request(self, pr):
        pr.fetch()
        print("Created branch {} tracking {}/{}".format(pr.head_ref,
                                                        pr.head_user.username,
                                                        pr.head_ref))
        print("Merge {} into {}".format(pr.head_ref, pr.base_ref))


class Cmd_WhoAmI(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._user = args.user

    def run(self):
        if self._user is None:
            print(self._auth.get_username())
        else:
            path = os.path.expanduser('~/.gizzconfig')
            with open(path, 'w') as out:
                print(self._user, file=out)
