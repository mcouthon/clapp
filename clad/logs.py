from colorama import Fore


class Logger(object):
    def red(self, msg):
        return Fore.RED + msg + Fore.RESET

    def yellow(self, msg):
        return Fore.YELLOW + msg + Fore.RESET

    def green(self, msg):
        return Fore.GREEN + msg + Fore.RESET

    def blue(self, msg):
        return Fore.BLUE + msg + Fore.RESET

    def error(self, msg, should_exit=True):
        print self._get_red(msg)
        if should_exit:
            exit(1)

    def log(self, repo, line):
        repo = Fore.GREEN + repo
        print '{0:<35}| {1}{2}'.format(repo, line, Fore.RESET)

    def header(self, header):
        header = self.blue(header)
        print '{s:{c}^{n}}'.format(s=header, n=40, c='-')

    def log_multiline(self, repo, output):
        for line in output.split('\n'):
            if line:
                line = Fore.YELLOW + line
                self.log(repo, line)

    def log_status(self, line, repo):
        if not line:
            return

        if len(line.split()) == 2:
            status_out, line = line.split()
            status_out = Fore.RED + status_out
            line = Fore.GREEN + line
            line = '{0} {1}'.format(status_out, line)
        else:
            line = Fore.GREEN + line

        self.log(repo, line)

    def log_install(self, line, name, verbose):
        if not line:
            return

        if verbose or line.startswith('Successfully installed'):
            line = Fore.YELLOW + line
            self.log(name, line)


logger = Logger()
