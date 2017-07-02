import os

from .constants import REPO_BASE


def get_repo_path(repo):
    return os.path.join(REPO_BASE, repo)
