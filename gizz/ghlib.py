import json
import urllib.request
import http.client
import base64
from gizz.utils import *

HOSTNAME = 'api.github.com'

class _Request:

    def __init__(self, location):
        self.post_object = None
        self._url_params = {}
        self._location = location
        self.method = 'GET'
        self.requires_auth = False

    def add_url_param(self, key, param):
        self._url_params[key] = param

    def perform(self):
        if self.post_object is None:
            json_data = None
        else:
            json_data = json.dumps(self.post_object)
        location = self._location.format(**self._url_params)
        headers = {}
        if self.requires_auth:
            encoded = base64.b64encode(("{}:{}".format(self.username,
                                                       self.password)).encode())
            headers['Authorization'] = b'Basic ' + encoded

        conn = http.client.HTTPSConnection(HOSTNAME)
        conn.request(self.method, location, body=json_data, headers=headers)
        resp = conn.getresponse()
        self._recv_data = resp.read()

    def get_response(self):
        return json.loads(self._recv_data.decode())


class LazyLoader:

    def __getattr__(self, name):
        # the class doesn't have the attribute so try and load it from the
        # remote store
        self._load()

        return self.__getattribute__(name)


class User(LazyLoader):

    def __init__(self, username, data=None):
        self.username = username
        if data is not None:
            self._load_from_data(data)

    def _load_from_data(self, data):
        self.name = data['name']
        self.following = data['following']

    def _load(self):
        r = _Request('/users/{user}')
        r.add_url_param('user', self.username)
        r.perform()
        data = r.get_response()
        self._load_from_data(data)

    def get_repo_list(self):
        r = _Request('/users/{user}/repos')
        r.add_url_param('user', self.username)
        r.perform()
        repos_data = r.get_response()

        repos = []
        for repo_data in repos_data:
            repo = Repository(self, repo_data['name'], repo_data)
            repos.append(repo)
            
        return repos


class Repository(LazyLoader):

    def __init__(self, user, reponame, data=None):
        self.user = user
        self.reponame = reponame
        if data is not None:
            self._load_from_data(data)

    def _load_from_data(self, data):
        self.git_url = data['git_url']
        self.description = data['description']

    def _load(self):
        r = _Request('/repos/{user}/{repo}')
        r.add_url_param('user', self.user.username)
        r.add_url_param('repo', self.reponame)
        r.perform()
        data = r.get_response()
        self._load_from_data(data)

    def get_branch_list(self):
        r = _Request('/repos/{user}/{repo}/branches')
        r.add_url_param('user', self.user.username)
        r.add_url_param('repo', self.reponame)
        r.perform()
        branches_data = r.get_response()

        branches = []
        for branch_data in branches_data:
            branch = Branch(self, branch_data['name'],
                            branch_data['commit']['sha'],
                            branch_data['commit']['url'])
            branches.append(branch)

        return branches

    def get_tag_list(self):
        r = _Request('/repos/{user}/{repo}/tags')
        r.add_url_param('user', self.user.username)
        r.add_url_param('repo', self.reponame)
        r.perform()
        tags_data = r.get_response()

        tags = []
        for tag_data in tags_data:
            tag = Tag(self, tag_data['name'],
                            tag_data['commit']['sha'],
                            tag_data['tarball_url'])
            tags.append(tag)

        return tags

    def get_pull_request_list(self):
        r = _Request('/repos/{user}/{repo}/pulls')
        r.add_url_param('user', self.user.username)
        r.add_url_param('repo', self.reponame)
        r.perform()
        pull_reqs_data = r.get_response()

        pull_reqs = []
        for pull_req_data in pull_reqs_data:
            pull_req = PullRequest(self.user, self, pull_req_data['number'],
                                   pull_req_data['title'],
                                   pull_req_data['body'])
            pull_reqs.append(pull_req)

        return pull_reqs

    def get_pull_request(self, id):
        r = _Request('/repos/{user}/{repo}/pulls/{id}')
        r.add_url_param('user', self.user.username)
        r.add_url_param('repo', self.reponame)
        r.add_url_param('id', id)
        r.perform()
        pull_req_data = r.get_response()

        pull_req = PullRequest(self.user, self, id,
                               pull_req_data['title'],
                               pull_req_data['body'])

        return pull_req

    def fork(self):
        r = _Request('/repos/{user}/{repo}/forks')
        r.add_url_param('user', self.user.username)
        r.add_url_param('repo', self.reponame)
        r.method = 'POST'
        r.requires_auth = True
        r.username = self.auth.get_username()
        r.password = self.auth.get_password()
        r.perform()
        repo_data = r.get_response()
        return Repository(Users(self.auth.get_username()), self.reponame,
                          data=repo_data)

    def __str__(self):
        return "{user}/{repo}".format(user=self.user.username,
                                      repo=self.reponame)

    def dump(self):
        print("{user}/{repo} => {git_url}".format(user=self.user.username,
                                                  repo=self.reponame,
                                                  git_url=self.git_url))
        print(self.description)


class Branch:

    def __init__(self, repo, name, sha, url):
        self.repo = repo
        self.name = name
        self.sha = sha
        self.url = url

    def dump(self):
        print(self.repo, self.name, self.sha)
        print(self.url)


class Tag:

    def __init__(self, repo, name, sha, tarball_url):
        self.repo = repo
        self.name = name
        self.sha = sha
        self.tarball_url = tarball_url

    def dump(self):
        print(self.repo, self.name, self.sha)
        print(self.tarball_url)


class PullRequest(LazyLoader):

    def __init__(self, base_user, repo, id, title, body, data=None):
        self.base_user = base_user
        self.repo = repo
        self.id = id
        self.title = title
        self.body = body

    def _load_from_data(self, data):
        self.head_user = User(data['head']['user']['login'])
        self.head_label = data['head']['label']
        self.head_ref = data['head']['ref']
        self.head_git_url = data['head']['repo']['git_url']
        self.base_ref = data['base']['ref']

    def _load(self):
        r = _Request('/repos/{user}/{repo}/pulls/{id}')
        r.add_url_param('user', self.base_user.username)
        r.add_url_param('repo', self.repo.reponame)
        r.add_url_param('id', self.id)
        r.perform()
        data = r.get_response()
        self._load_from_data(data)

    def fetch(self):
        git_run('remote', 'add', self.head_user.username, self.head_git_url)
        git_run('fetch', self.head_user.username)
        git_run('branch', self.head_ref,
                '{}/{}'.format(self.head_user.username, self.head_ref))
