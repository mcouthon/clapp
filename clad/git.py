import os
import sh

from .logs import Logger
from .utils import get_repo_path
from .constants import BASE_GITHUB_URL


class Git(object):
    def __init__(self, repo=None):
        self._git = self._get_git(repo)
        self._repo = repo
        self.logger = Logger()

    def _validate_git(self):
        try:
            sh.git
        except sh.CommandNotFound:
            self.logger.error('git is not installed on the computer')

    def validate_repo(self, repo=None):
        repo = repo or self._repo
        repo_path = get_repo_path(repo)
        msg = None
        if not os.path.exists(repo_path):
            msg = 'Folder `{0}` does not exist'.format(repo_path)
            return self.logger.red(msg)

        try:
            self._git.status()
        except sh.ErrorReturnCode, e:
            if 'Not a git repository' in str(e):
                msg = '`{0}` is not a git repository'.format(repo_path)
            else:
                msg = str(e)
            return self.logger.red(msg)

        return None

    def status(self):
        return self._git('status', '-s').strip()

    def _get_git(self, repo=None):
        self._validate_git()
        if not repo:
            return sh.git.bake()

        repo_path = get_repo_path(repo)
        return sh.git.bake(
            '--no-pager',
            '--git-dir', os.path.join(repo_path, '.git'),
            '--work-tree', repo_path)

    def get_current_branch_or_tag(self, hide_tags=False):
        """
        Get the value of HEAD, if it's not detached, or emit the 
        tag name, if it's an exact match. Throw an error otherwise
        """
        branch = self._git('rev-parse', '--abbrev-ref', 'HEAD').strip()
        if hide_tags:
            return branch

        tags = self._git('tag', '--points-at', 'HEAD').split()
        result = branch if branch != 'HEAD' else ''

        if tags:
            tags = ', '.join(tags)
            tags = self.logger.yellow('[{0}]'.format(tags))
            result = '{0} {1}'.format(result, tags).strip()
        return result

    def pull(self):
        return self._git.pull()

    def checkout(self, branch):
        return self._git.checkout(branch)

    def _git_clone(self, repo, branch, shallow):
        full_url = BASE_GITHUB_URL.format(repo)
        args = [full_url, get_repo_path(repo), '--branch', branch]
        if shallow:
            args += ['--depth', 1]
        self._git.clone(*args)

    def clone_repo(self, repo, repo_branch, shallow):
        self.logger.log_multiline(repo, 'Cloning `{0}`'.format(repo))
        if self.validate_repo(repo):
            return self.logger.yellow('Folder already exists. '
                                      'Repo probably already cloned')
        else:
            self._git_clone(repo, repo_branch, shallow)
            return self.logger.green('Successfully cloned `{0}`'.format(repo))
