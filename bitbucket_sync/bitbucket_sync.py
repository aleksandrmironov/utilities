#!/usr/bin/env python
try:
    import json
except ImportError:
    import simplejson as json
import optparse
import os
import subprocess
import sys
import urllib2


def _get_repositories(owner, username, password):
    auth_value = ('%s:%s' % (username, password)).encode('base64').strip()
    headers = {'Authorization': 'Basic %s' % auth_value}
    url = 'https://bitbucket.org/api/2.0/repositories/%s?role=member' % owner
    values = []

    while url is not None:
        request = urllib2.Request(url, None, headers)
        data = json.loads(urllib2.urlopen(request).read())
        values = values + data['values']
        url = data.get('next')

    return values


def _git_clone(username, password, directory, sub_dir_name, owner, slug, verbose=False):
    os.chdir(directory)
    cmd = 'git clone --mirror https://%s:%s@bitbucket.org/%s/%s.git %s' % (username, password,
                                                                  owner, slug, sub_dir_name)
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    ret_value = proc.wait()
    msg = proc.stdout.read()
    sys.stdout.write('%s%s%s%s' % (sub_dir_name, os.linesep,
                                   '=' * len(sub_dir_name), os.linesep))
    sys.stdout.write("%s%s" % (msg, os.linesep))
    return ret_value


def _git_pull(directory, sub_dir_name, owner, slug, verbose=False):
    working_dir = os.path.join(directory, sub_dir_name)
    os.chdir(working_dir)
    cmd = 'git pull --all'
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    ret_value = proc.wait()
    msg = proc.stdout.read()
    if verbose or not "no changes found" in msg:
        sys.stdout.write('%s%s%s%s' % (sub_dir_name, os.linesep,
                                       '=' * len(sub_dir_name), os.linesep))
        sys.stdout.write("%s%s" % (msg, os.linesep))
    return ret_value


if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-u', '--username', action='store',
                      default=os.environ.get('USER'),
                      help='Your username on bitbucket.org '
                           '[Defaults to your system user name]')
    parser.add_option('-p', '--password', action='store',
                      help='Your password on bitbucket.org')
    parser.add_option('-o', '--owner', action='store',
                      help='Owner of repositories on bitbucket.org')
    parser.add_option('-d', '--directory', action='store', default=os.getcwd(),
                      help='The local directory to sync to [Defaults to '
                           'the current directory]')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose',
                      help='Verbose output')
    (options, args) = parser.parse_args()

    if not options.username:
        parser.error('Username is required')
    if not options.password:
        parser.error('Password is required')
    if not os.path.isdir(options.directory):
        os.makedirs(options.directory)

    sub_dirs = os.walk(options.directory).next()[1]

    for repo_data in _get_repositories(options.owner, options.username, options.password):
        (owner, slug) = repo_data['full_name'].split('/')

        sub_dir_name = '%s__%s' % (slug, owner)
        fn_route = _git_clone if sub_dir_name not in sub_dirs else _git_pull
        fn_route(options.username, options.password, options.directory, sub_dir_name, owner, slug, options.verbose)
