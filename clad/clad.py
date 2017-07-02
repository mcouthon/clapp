#!/usr/bin/env python

import sh
import argh
from colorama import Fore
from threading import Thread

from .logs import logger
from .git import Git
from .repos import Repos
from .constants import MASTER
from .utils import get_repo_path


command = argh.EntryPoint(
    'clad',
    dict(description='Custom commands that run on several cloudify repos')
)


@command
def status(hide_tags=False):
    logger.header('Status')
    repos = Repos()
    for repo, _ in repos.repos:
        git = Git(repo)
        output = git.validate_repo()
        if output:
            logger.log(repo, output)
            continue

        branch = git.get_current_branch_or_tag(hide_tags=hide_tags)
        logger.log(repo, branch)

        for line in git.status().split('\n'):
            logger.log_status(line, repo)


@command
def pull():
    def _pull_repo(repo):
        git = Git(repo)
        try:
            output = git.pull()
        except sh.ErrorReturnCode:
            output = 'No upstream defined. Skipping pull.'
        logger.log_multiline(repo, output)

    logger.header('Pull')
    repos = Repos()
    threads = [Thread(target=_pull_repo, args=(repo, ))
               for repo, _ in repos.repos]
    for t in threads:
        t.daemon = True
        t.start()

    for t in threads:
        t.join()


@command
def install(verbose=False):
    logger.header('Install')
    pip = sh.pip.bake()
    repos = Repos()

    for name, path in repos.cloudify_packages:
        repo_path = get_repo_path(path)
        try:
            output = pip.install('-e', repo_path)
        except Exception, e:
            error = Fore.RED + 'Could not pip install repo: {0}'.format(e)
            logger.log(name, error)
            continue

        for line in output.split('\n'):
            logger.log_install(line, name, verbose)


@command
def checkout(branch, hide_tags=False):
    logger.header('Checkout')
    repos = Repos(branch)
    for repo, repo_branch in repos.repos:
        git = Git(repo)
        try:
            git.checkout(repo_branch)
            branch = git.get_current_branch_or_tag(hide_tags=hide_tags)
            logger.log(repo, branch)
        except sh.ErrorReturnCode:
            output = 'Could not checkout branch `{0}`'.format(repo_branch)
            logger.log_multiline(repo, output)


@command
def clone(shallow=False, dev=True):
    logger.header('Clone')
    git = Git()
    repos = Repos(dev=dev)
    repos.create_repo_base()

    for repo, repo_branch in repos.repos:
        try:
            output = git.clone_repo(repo, repo_branch, shallow)
        except sh.ErrorReturnCode, e:
            error = str(e)

            if 'fatal: destination path' in error:
                error = 'Repo is probably already cloned (the folder exists)'
            if 'fatal: Could not read from remote repository' in error:
                error = 'Make sure you have your GitHub SSH key set up'

            output = 'Could not clone repo `{0}`: {1}'.format(repo, error)
            output = logger.red(output)

        logger.log_multiline(repo, output)


@command
def setup(branch=MASTER, requirements=None):
    repos = Repos(branch=branch, requirements=requirements)

    clone(shallow=True)
    status()
    install()
