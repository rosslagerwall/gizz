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

import os.path
import re
import gizz.ghlib
from gizz.utils import *

class Cmd:

    gh_url = re.compile(r'^(?:git://github.com/|git@github.com:)(\w+)/(\w+)(?:\.git)?')

    def __init__(self):
        pass

    def set_authorizer(self, auth):
        self._auth = auth

    def _get_gh_name(self, remote_name):
        output = git_system('remote', '-v', 'show')
        for line in output.strip().split('\n'):
            name, url, _ = line.split()
            if name == remote_name:
                matches = self.gh_url.findall(url)
                if len(matches) > 0:
                    return matches[0]

        return (None, None)

    def _get_best_gh_name(self):
        user, repo = self._get_gh_name(self._auth.get_username())
        remote_name = self._auth.get_username()
        if user is None or repo is None:
            user, repo = self._get_gh_name('origin')
            remote_name = 'origin'
            if user is None or repo is None:
                # raise exception
                pass
        return user, repo, remote_name


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
            user, repo, _ = self._get_best_gh_name()
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
            user, repo, _ = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        for tag in repo.get_tag_list():
            print(tag.name, tag.sha[:10])


class Cmd_Fork(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo
        self._no_add = args.no_add

    def run(self):
        if self._arg_repo is None:
            user, repo = self._get_gh_name('origin')
            # TODO fail if user already owns the repo
            # TODO fail if None, None is returned
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        repo.auth = self._auth
        new_repo = repo.fork()
        if self._arg_repo is None and not self._no_add:
            new_repo.add_as_remote()


class Cmd_ListPullRequests(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo
        self._verbose = args.verbose
        self._id = args.id
        self._comments = args.comments
        self._closed = args.closed

    def _print(self, pr, verbose=True):
        if verbose:
            print("From:", pr.head.repo.user.username)
            print("Remote URL:", pr.head.git_url)
            print("Date:", pr.create_date)
            print("Id:", pr.id)
            print("Subject:", pr.title)
            print("Merge {} at {}\n   to {} at {}{}".format(
                    pr.head.name, pr.head.sha, pr.base.name, pr.base.sha,
                    " [auto-mergeable]" if pr.mergeable else ""))
            print(pr.body.strip())
        else:
            print(pr.id, '=>', pr.title)
        if self._comments:
            comments = pr.get_comments()
            if comments:
                print()
            for c in comments:
                print("Comment from:", c.user.username)
                print(c.body)

    def run(self):
        if self._arg_repo is None:
            user, repo, _ = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        if self._id:
            pr = repo.get_pull_request(self._id)
            self._print(pr)
        else:
            pr_list = repo.get_pull_request_list(closed=self._closed)
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
        self._automerge = args.merge

    def run(self):
        if self._arg_repo is None:
            user, repo, _ = self._get_best_gh_name()
        else:
            user, repo = self._arg_repo.split('/')
        repo = gizz.ghlib.Repository(gizz.ghlib.User(user), repo)
        if self._fetch_all:
            if self._automerge:
                raise InvalidArgumentException('--merge requires a specific id')
            for pr in repo.get_pull_request_list():
                self._fetch_one_pull_request(pr)
        else:
            pr = repo.get_pull_request(self._id)
            if self._automerge:
                pr.auth = self._auth
                sha, msg = pr.automerge()
                print(msg)
                if sha:
                    print('{} is now at {}'.format(pr.head.name, sha))
            else:
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
            try:
                print(self._auth.get_username())
            except UnknownUserException:
                print("Unknown user: set your GitHub username with gizz whoami")
        else:
            path = os.path.expanduser('~/.gizzconfig')
            with open(path, 'w') as out:
                print(self._user, file=out)


class Cmd_RequestPull(Cmd):

    def __init__(self, args):
        Cmd.__init__(self)
        self._arg_repo = args.repo
        self._head = args.head
        self._base = args.base
        self._no_push = args.no_push
        self._no_fork = args.no_fork

    def _get_repos_from_parent(self, user, reponame):
        head_repo = gizz.ghlib.Repository(gizz.ghlib.User(user), reponame)

        if self._arg_repo is None:
            base_repo = head_repo.parent
        else:
            u, r = self._arg_repo.split('/')
            base_repo = gizz.ghlib.Repository(gizz.ghlib.User(u), r)
        base_repo.auth = self._auth

        return head_repo, base_repo

    def _get_repos_fork(self, user, reponame):
        if self._arg_repo is None:
            base_repo = gizz.ghlib.Repository(gizz.ghlib.User(user), reponame)
        else:
            user, reponame = self._arg_repo.split('/')
            base_repo = gizz.ghlib.Repository(gizz.ghlib.User(user), reponame)
        base_repo.auth = self._auth

        if self._no_fork:
            raise ForkNeededException()
        head_repo = base_repo.fork()
        head_repo.add_as_remote()

        return head_repo, base_repo

    def _get_repos_from_remote(self, remote_origin, remote_username):
        if self._arg_repo is None:
            base_repo = gizz.ghlib.Repository(gizz.ghlib.User(remote_origin[0]),
                                              remote_origin[1])
        else:
            user, reponame = self._arg_repo.split('/')
            base_repo = gizz.ghlib.Repository(gizz.ghlib.User(user), reponame)
        base_repo.auth = self._auth

        head_repo = gizz.ghlib.Repository(
            gizz.ghlib.User(remote_username[0]), remote_username[1])

        return head_repo, base_repo

    def run(self):
        if self._head is None:
            output = git_system('branch')
            for line in output.split("\n"):
                if line.startswith('*'):
                    head = line[2:]
        else:
            head = self._head

        # figure out what the base and head repos are
        # if the user does not have a Git remote either as origin or <username>
        # which is a personal GitHub repo, fork the base repo to get one
        auth_username = self._auth.get_username()
        remote_origin = self._get_gh_name('origin')
        remote_username = self._get_gh_name(auth_username)
        if remote_origin[0] == auth_username:
            head_repo, base_repo = self._get_repos_from_parent(*remote_origin)
            push_name = 'origin'
        elif remote_username == (None, None):
            head_repo, base_repo = self._get_repos_fork(*remote_origin)
            push_name = auth_username
        elif remote_username[0] == auth_username:
            head_repo, base_repo = self._get_repos_from_remote(remote_origin,
                                                               remote_username)
            push_name = auth_username
        else:
            # TODO error
            pass

        if not self._no_push:
            # attempt to push the local branch to the remote repo
            git_run('push', push_name, head)

        # get the title and body for the pr
        m = TitledMessageGetter()
        edit_result = m.edit()
        if edit_result is None:
            print("Pull request cancelled")
        else:
            source = gizz.ghlib.Branch(head_repo, head)
            target = gizz.ghlib.Branch(base_repo, self._base)
            target.create_pull_request(edit_result[0], edit_result[1], source)
