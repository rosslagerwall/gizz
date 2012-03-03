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
            user, repo = self._get_gh_name('origin')
            # TODO fail if user already owns the repo
            # TODO fail if None, None is returned
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        repo.auth = self._auth
        repo.fork()


class Cmd_ListPullRequests(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo
        self._verbose = args.verbose
        self._id = args.id

    def _print(self, pr, verbose=True):
        if verbose:
            print("From:", pr.head.repo.user.username)
            print("Remote URL:", pr.head.git_url)
            print("Date:", pr.create_date)
            print("Id:", pr.id)
            print("Subject:", pr.title)
            print("Merge {} at {}\n   to {} at {}".format(
                    pr.head.name, pr.head.sha, pr.base.name, pr.base.sha))
            print(pr.body.strip())
        else:
            print(pr.id, '=>', pr.title)

    def run(self):
        if self._arg_repo is None:
            user, repo = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        if self._id:
            pr = repo.get_pull_request(self._id)
            self._print(pr)
        else:
            pr_list = repo.get_pull_request_list()
            for i, pr in enumerate(pr_list):
                if self._verbose and i != 0:
                    print('--')
                self._print(pr, self._verbose)

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
        fetched_branch = pr.fetch()
        username = pr.head.repo.user.username
        print("Created branch {} tracking {}/{}".format(fetched_branch,
                                                        username,
                                                        pr.head.name))
        print("Merge {} into {}".format(fetched_branch, pr.base.name))


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
