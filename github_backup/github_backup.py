#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from pygithub3 import Github
import argparse
import os
import tarfile
import shutil
import time
import boto
from boto.s3.key import Key


def cli_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-id', action='store',
                    dest='aws_access_key_id',
                    help='aws_access_key_id',
                    required=True)

    parser.add_argument('-key', action='store',
                    dest='aws_secret_access_key',
                    help='aws_secret_access_key',
                    required=True)

    parser.add_argument('-region', action='store',
                    dest='aws_region',
                    help='aws_region',
                    default='eu-west-1')

    parser.add_argument('-o', action='store',
                        dest='organization',
                        help='Organization name',
                        required=True)

    parser.add_argument('-b', action='store',
                        dest='bucket_name',
                        help='S3 bucket to save backups',
                        required=True)

    parser.add_argument('-t', action='store',
                        dest='token',
                        help='Secret app token',
                        required=True)

    parser.add_argument('-d', action='store',
                        dest='directory', default='/tmp/github_backup',
                        help='Cloning output directory')

    parser.add_argument('-a', action='store',
                        dest='archive',
                        help='Output archive name without extension')

    parser.add_argument('-m', action='store_true',
                        dest='mirror', default=True,
                        help='Enable mirror clone')

    parser.add_argument('-e', action='store_true',
                        dest='dateext', default=True,
                        help='add datetime ext to the archive filename')

    parser.add_argument('-g', action='store',
                        dest='git', type=str, default='',
                        help='Additional git params')

    return parser.parse_args()


def get_repos(args):
    config = {'token': args.token}
    gh = Github(**config)

    return gh.repos.list_by_org(args.organization).all()


def clone_repo(repo_list,args):

    if os.path.isdir(args.directory):
        shutil.rmtree(args.directory)

    os.mkdir(args.directory)

    if args.mirror is True:
        args.git += " --mirror"

    for repo in repo_list:
        repo_url = "https://%(token)s:x-oauth-basic@github.com/%(organization)s/%(repo)s.git" % {'token': args.token,
                                                                                                 'organization': args.organization,
                                                                                                 'repo': repo.name}

        os.system('git clone %(arguments)s %(repo_url)s %(directory)s/%(repo)s' % {'arguments': args.git,
                                                                                   'repo_url': repo_url,
                                                                                   'directory': args.directory, 'repo': repo.name})


def create_archive(output_filename, source_directory):

    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_directory, arcname=os.path.basename(source_directory))

    if os.path.isdir(source_directory):
        shutil.rmtree(source_directory)

def upload_to_s3(aws_access_key_id, aws_secret_access_key, file, bucket, key, callback=None, md5=None,
                 reduced_redundancy=False, content_type=None):
    conn = boto.connect_s3(aws_access_key_id, aws_secret_access_key)
    bucket = conn.get_bucket(bucket, validate=True)
    k = Key(bucket)
    k.key = key
    if content_type:
        k.set_metadata('Content-Type', content_type)

    sent = k.set_contents_from_file(file, cb=callback, num_cb=100, md5=md5, reduced_redundancy=reduced_redundancy, rewind=True)
    return sent

def main():
    args = cli_args()

    repo_list = get_repos(args)
    clone_repo(repo_list,args)

    if args.archive:
        dest_file = args.archive
    else:
        dest_file = args.directory

    if args.dateext is True:
        timestamp = time.strftime('%Y%m%d-%H%M%S')
        dest_file = "%s%s" % (dest_file, timestamp)

    dest_file = "%s.tgz" % dest_file

    create_archive(dest_file, args.directory)

    file = open(dest_file, 'r+')
    s3_item_key = dest_file.rsplit('/')[-1:]
    upload_to_s3(args.aws_access_key_id, args.aws_secret_access_key, file, args.bucket_name, s3_item_key[0])


if __name__ == "__main__":
    main()