import os
from collections import OrderedDict

from .constants import MASTER, REPO_BASE


class Repos(object):
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

    def __init__(self, branch=MASTER, dev=True, requirements=None):
        self._branch = branch
        self._full_repos_list = self.REPOS if dev else self.CORE_REPOS
        if requirements:
            self._repos = self._parse_requirements(requirements)
        else:
            self._repos = OrderedDict((repo, branch) 
                                      for repo in self._full_repos_list)

    @property
    def repos(self):
        return self._repos.iteritems()

    # def _get_repos(self, branch=MASTER, dev=True):
    #     if self._repos:
    #         if branch != MASTER:
    #             for repo, repo_branch in self._repos.iteritems():
    #                 if repo_branch == MASTER:
    #                     self._repos[repo] = branch
    #         return self._repos.iteritems()
    #     else:
    #         repos_list = self._REPOS if dev else CORE_REPOS
    #         # This will maintain proper order
    #         repo_dict = 
    #         return repo_dict.iteritems()

    def _parse_requirements(self, requirements):
        repos_dict = {}
        with open(requirements, 'r') as f:
            for line in f.readlines():
                line = line.strip()
                if '@' in line:
                    repo, repo_branch = line.split('@')
                else:
                    repo, repo_branch = line, self._branch
                repos_dict[repo] = repo_branch

        result_dict = OrderedDict()
        # This extra loop makes sure the order of the repos in the dict is
        # correct
        for repo in self._full_repos_list:
            if repo in repos_dict:
                result_dict[repo] = repos_dict[repo]

        return result_dict

    @property
    def cloudify_packages(self):
        packages = OrderedDict()
        for repo, _ in self.repos:
            packages[repo] = repo

        manager_repo = packages.pop('cloudify-manager', None)
        packages.pop('cloudify-manager-blueprints', None)
        packages.pop('cloudify-dev', None)

        if manager_repo:
            packages['cloudify-rest-service'] = 'cloudify-manager/rest-service'
            packages['cloudify-integration-tests'] = 'cloudify-manager/tests'
            packages['cloudify-system-workflows'] = 'cloudify-manager/workflows'
        return packages.iteritems()

    @staticmethod
    def create_repo_base():
        if not os.path.exists(REPO_BASE):
            print 'Creating base repos dir: {0}'.format(REPO_BASE)
            os.makedirs(REPO_BASE)
