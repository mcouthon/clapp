import os

MASTER = 'master'
REPO_BASE = os.environ.get('CLAD_REPO_BASE',
                           os.path.expanduser('~/dev/repos/'))
BASE_GITHUB_URL = 'git@github.com:cloudify-cosmo/{0}.git'
