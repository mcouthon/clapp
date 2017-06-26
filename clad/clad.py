#!/usr/bin/env python

import os
import sh
import argh
from colorama import Fore
from threading import Thread
from collections import OrderedDict


MASTER = 'master'
CORE_REPOS = [
    'cloudify-dsl-parser',
    'cloudify-rest-client',
    'cloudify-plugins-common',
    'cloudify-diamond-plugin',
    'cloudify-agent',
    'cloudify-cli',
    'cloudify-manager',
    'cloudify-manager-blueprints',
    'cloudify-premium',
    'cloudify-script-plugin',
    'cloudify-amqp-influxdb',
    'docl'
]
DEV_REPOS = [
    'cloudify-fabric-plugin',
    'cloudify-system-tests',
    'cloudify-dev'
]
REPOS = CORE_REPOS + DEV_REPOS

REPO_BASE = os.environ.get('CLAD_REPO_BASE',
                           os.path.expanduser('~/dev/repos/'))
BASE_GITHUB_URL = 'git@github.com:cloudify-cosmo/{0}.git'

# The actual map of repos to clone/checkout/pull/install, as calculated
# from the REPOS list along with any requirements file passed to clad
actual_repos = OrderedDict()

command = argh.EntryPoint(
    'clad',
    dict(description='Custom commands that run on several cloudify repos')
)


def _get_error(msg):
    return Fore.RED + msg + Fore.RESET


def _print_error(msg, should_exit=True):
    print _get_error(msg)
    if should_exit:
        exit(1)


def _repo_path(repo):
    return os.path.join(REPO_BASE, repo)


def _validate_git():
    try:
        sh.git
    except sh.CommandNotFound:
        _print_error('git is not installed on the computer')


def _validate_repo(repo, git):
    repo_path = _repo_path(repo)
    msg = None
    if not os.path.exists(repo_path):
        msg = 'Folder `{0}` does not exist'.format(repo_path)
        return _get_error(msg)

    try:
        git.status()
    except sh.ErrorReturnCode, e:
        if 'Not a git repository' in str(e):
            msg = '`{0}` is not a git repository'.format(repo_path)
        else:
            msg = str(e)
        return _get_error(msg)

    return None


def _git(repo=None):
    _validate_git()
    if not repo:
        return sh.git.bake()

    repo_path = _repo_path(repo)
    return sh.git.bake(
        '--no-pager',
        '--git-dir', os.path.join(repo_path, '.git'),
        '--work-tree', repo_path)


def _print(repo, line):
    repo = Fore.GREEN + repo
    print '{0:<35}| {1}{2}'.format(repo, line, Fore.RESET)


def _print_header(header):
    header = Fore.BLUE + header + Fore.RESET
    print '{s:{c}^{n}}'.format(s=header, n=40, c='-')


def _get_current_branch_or_tag(git, hide_tags=False):
    """
    Get the value of HEAD, if it's not detached, or emit the tag name, if it's
    an exact match. Throw an error otherwise
    """
    branch = git('rev-parse', '--abbrev-ref', 'HEAD').strip()
    if hide_tags:
        return branch

    tags = git('tag', '--points-at', 'HEAD').split()
    result = branch if branch != 'HEAD' else ''

    if tags:
        tags = ', '.join(tags)
        tags = Fore.YELLOW + '[{0}]'.format(tags) + Fore.RESET
        result = '{0} {1}'.format(result, tags).strip()
    return result


def _parse_and_print_output(repo, output):
    for line in output.split('\n'):
        if line:
            line = Fore.YELLOW + line
            _print(repo, line)


def _pull_repo(repo):
    git = _git(repo)
    try:
        output = git.pull()
    except sh.ErrorReturnCode:
        output = 'No upstream defined. Skipping pull.'
    _parse_and_print_output(repo, output)


def _get_repos(branch=MASTER, dev=True):
    if actual_repos:
        if branch != MASTER:
            for repo, repo_branch in actual_repos.iteritems():
                if repo_branch == MASTER:
                    actual_repos[repo] = branch
        return actual_repos.iteritems()
    else:
        repos_list = REPOS if dev else CORE_REPOS
        return {repo: branch for repo in repos_list}.iteritems()


def _parse_requirements(requirements, branch):
    repos_dict = {}
    with open(requirements, 'r') as f:
        for line in f.readlines():
            line = line.strip()
            if '@' in line:
                repo, repo_branch = line.split('@')
            else:
                repo, repo_branch = line, branch
            repos_dict[repo] = repo_branch

    # This extra loop makes sure the order of the repos in the dict is correct
    for repo in REPOS:
        if repo in repos_dict:
            actual_repos[repo] = repos_dict[repo]


def _get_cloudify_packages():
    packages = OrderedDict()
    for repo, _ in _get_repos():
        packages[repo] = repo

    manager_repo = packages.pop('cloudify-manager', None)
    packages.pop('cloudify-manager-blueprints', None)
    packages.pop('cloudify-dev', None)

    if manager_repo:
        packages['cloudify-rest-service'] = 'cloudify-manager/rest-service'
        packages['cloudify-integration-tests'] = 'cloudify-manager/tests'
        packages['cloudify-system-workflows'] = 'cloudify-manager/workflows'
    return packages.iteritems()


def _git_clone(git, repo, branch, shallow):
    full_url = BASE_GITHUB_URL.format(repo)
    repo_path = os.path.join(REPO_BASE, repo)
    args = [full_url, repo_path, '--branch', branch]
    if shallow:
        args += ['--depth', 1]
    git.clone(*args)


def _clone_repo(git, repo, repo_branch, shallow):
    _parse_and_print_output(repo, 'Cloning `{0}`'.format(repo))
    _git_clone(git, repo, repo_branch, shallow)
    return Fore.GREEN + 'Successfully cloned `{0}`'.format(repo) + Fore.RESET


def _create_repo_base():
    if not os.path.exists(REPO_BASE):
        print 'Creating base repos dir: {0}'.format(REPO_BASE)
        os.makedirs(REPO_BASE)


def _print_status_line(line, repo):
    if not line:
        return

    if len(line.split()) == 2:
        status_out, line = line.split()
        status_out = Fore.RED + status_out
        line = Fore.GREEN + line
        line = '{0} {1}'.format(status_out, line)
    else:
        line = Fore.GREEN + line

    _print(repo, line)


def _print_install_line(line, name, verbose):
    if not line:
        return

    if verbose or line.startswith('Successfully installed'):
        line = Fore.YELLOW + line
        _print(name, line)


@command
def status(hide_tags=False):
    _print_header('Status')
    for repo, _ in _get_repos():
        git = _git(repo)
        output = _validate_repo(repo, git)
        if output:
            _print(repo, output)
            continue

        branch = _get_current_branch_or_tag(git, hide_tags=hide_tags)
        _print(repo, branch)

        status_out = git('status', '-s').strip()
        for line in status_out.split('\n'):
            _print_status_line(line, repo)


@command
def pull():
    _print_header('Pull')
    threads = [Thread(target=_pull_repo, args=(repo, ))
               for repo, _ in _get_repos()]
    for t in threads:
        t.daemon = True
        t.start()

    for t in threads:
        t.join()


@command
def install(verbose=False):
    _print_header('Install')
    pip = sh.pip.bake()

    for name, path in _get_cloudify_packages():
        repo_path = os.path.join(REPO_BASE, path)
        try:
            output = pip.install('-e', repo_path)
        except Exception, e:
            error = Fore.RED + 'Could not pip install repo: {0}'.format(e)
            _print(name, error)
            continue

        for line in output.split('\n'):
            _print_install_line(line, name, verbose)


@command
def checkout(branch, hide_tags=False):
    _print_header('Checkout')
    for repo, repo_branch in _get_repos(branch):
        git = _git(repo)
        try:
            git.checkout(repo_branch)
            branch = _get_current_branch_or_tag(git, hide_tags=hide_tags)
            _print(repo, branch)
        except sh.ErrorReturnCode:
            output = 'Could not checkout branch `{0}`'.format(repo_branch)
            _parse_and_print_output(repo, output)


@command
def clone(shallow=False, dev=True):
    _print_header('Clone')
    git = _git()
    _create_repo_base()

    for repo, repo_branch in _get_repos(dev=dev):
        try:
            output = _clone_repo(git, repo, repo_branch, shallow)
        except sh.ErrorReturnCode, e:
            error = str(e)

            if 'fatal: destination path' in error:
                error = 'Repo is probably already cloned (the folder exists)'
            if 'fatal: Could not read from remote repository' in error:
                error = 'Make sure you have your GitHub SSH key set up'

            output = 'Could not clone repo `{0}`: {1}'.format(repo, error)
            output = _get_error(output)

        _parse_and_print_output(repo, output)


@command
def setup(branch=MASTER, requirements=None):
    if requirements:
        _parse_requirements(requirements, branch)

    clone(shallow=True)
    status()
    install()
