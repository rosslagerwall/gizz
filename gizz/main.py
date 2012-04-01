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

import sys
import argparse
from gizz.builtins import *

# a factory to get the correct Command object based on the user input.
def get_command(subcommand, args):
    if subcommand == 'whoami':
        return Cmd_WhoAmI(args)
    elif subcommand == 'list-branches':
        return Cmd_ListBranches(args)
    elif subcommand == 'list-tags':
        return Cmd_ListTags(args)
    elif subcommand == 'fetch-pr':
        return Cmd_FetchPullRequest(args)
    elif subcommand == 'list-repos':
        return Cmd_ListRepos(args)
    elif subcommand == 'list-pr':
        return Cmd_ListPullRequests(args)
    elif subcommand == 'fork':
        return Cmd_Fork(args)
    elif subcommand == 'request-pull':
        return Cmd_RequestPull(args)
    else:
        pass
        # TODO

def run():
    parser = argparse.ArgumentParser(prog='gizz')
    subparsers = parser.add_subparsers(dest='subcommand',
                                       help='choose a subcommand')

    cmd_list_repos = subparsers.add_parser('list-repos', help='a help')
    cmd_list_repos.add_argument('user', type=str, help='list for user',
                                default=None, nargs='?')

    cmd_list_branches = subparsers.add_parser('list-branches', help='a help')
    cmd_list_branches.add_argument('--repo', type=str,
                                   help='list branches of REPO')

    cmd_list_tags = subparsers.add_parser('list-tags', help='a help')
    cmd_list_tags.add_argument('--repo', type=str,
                               help='list tags of REPO')

    cmd_fork = subparsers.add_parser('fork', help='a help')
    cmd_fork.add_argument('-n', '--no-add',
                          help="don't add new repository as a remote",
                          action='store_true')
    cmd_fork.add_argument('--repo', type=str,
                               help='fork REPO')

    cmd_list_pr = subparsers.add_parser('list-pr', help='a help')
    cmd_list_pr.add_argument('-v', '--verbose', help='more details',
                             action='store_true')
    cmd_list_pr.add_argument('-c', '--comments', help="show comments",
                                action='store_true')
    cmd_list_pr.add_argument('--repo', type=str,
                             help='list pull requests of REPO')
    cmd_list_pr.add_argument('id', type=int, help='list request #id',
                              default=None, nargs='?')

    cmd_fetch_pr = subparsers.add_parser('fetch-pr',
                                         help='fetch a pull request into a '
                                         'local branch')
    cmd_fetch_pr.add_argument('--repo', type=str,
                              help='fetch request from REPO')
    cmd_fetch_pr.add_argument('id', type=int, help='fetch request #id',
                              default=None, nargs='?')

    cmd_whoami = subparsers.add_parser('whoami',
                                       help='get or set your GitHub username')
    cmd_whoami.add_argument('user', type=str, help='set username to user',
                            default=None, nargs='?')

    cmd_req_pull = subparsers.add_parser('request-pull',
                                         help='create a pull request on GitHub')
    cmd_req_pull.add_argument('-r', '--repo', type=str,
                              help='send request to REPO')
    cmd_req_pull.add_argument('-b', '--base', type=str,
                              help='remote branch (default: master)',
                              default='master')
    cmd_req_pull.add_argument('-e', '--head', type=str,
                              help='local branch (default: current branch)',
                              default=None)
    cmd_req_pull.add_argument('-p', '--no-push',
                              help="don't push to the remote branch",
                              action='store_true')
    cmd_req_pull.add_argument('-f', '--no-fork',
                              help="don't fork the parent repo",
                              action='store_true')

    args = parser.parse_args()
    command = get_command(args.subcommand, args)
    ug = StoredUsernameGrabber()
    pg = BasicPasswordGrabber()
    command.set_authorizer(Authorizer(ug, pg))
    try:
        command.run()
    except Exception as e:
        print(e, file=sys.stderr)
