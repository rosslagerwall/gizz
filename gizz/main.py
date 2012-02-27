import argparse
from gizz.builtins import *

# a factory to get the correct Command object based on the user input.
def get_command(subcommand, args):
    if subcommand == 'whoami':
        return Cmd_WhoAmI(args)
    elif subcommand == 'list-branches':
        return Cmd_ListBranches(args)
    elif subcommand == 'fetch-pr':
        return Cmd_FetchPullRequest(args)
    elif subcommand == 'list-repos':
        return Cmd_ListRepos(args)
    elif subcommand == 'list-pr':
        return Cmd_ListPullRequests(args)
    elif subcommand == 'fork':
        return Cmd_Fork(args)
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

    cmd_list_fork = subparsers.add_parser('fork', help='a help')
    cmd_list_fork.add_argument('--repo', type=str,
                               help='fork REPO')

    cmd_list_pr = subparsers.add_parser('list-pr', help='a help')
    cmd_list_pr.add_argument('--repo', type=str,
                             help='list pull requests of REPO')

    cmd_fetch_pr = subparsers.add_parser('fetch-pr',
                                         help='fetch a pull request into a '
                                         'local branch')
    cmd_fetch_pr.add_argument('--repo', type=str,
                              help='fetch request from REPO')
    cmd_fetch_pr.add_argument('id', type=int, help='fetch request #id')

    cmd_whoami = subparsers.add_parser('whoami',
                                       help='get or set your GitHub username')
    cmd_whoami.add_argument('user', type=str, help='set username to user',
                            default=None, nargs='?')

    args = parser.parse_args()
    command = get_command(args.subcommand, args)
    ug = StoredUsernameGrabber()
    pg = BasicPasswordGrabber()
    command.set_authorizer(Authorizer(ug, pg))
    command.run()
