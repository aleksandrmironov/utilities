#!/usr/bin/python
import boto.ec2
import argparse

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

parser.add_argument('-project', action='store',
                    dest='project_name',
                    help='project_name',
                    required=True)

cli_args = parser.parse_args()

tags_to_sync = ['Name', 'group', 'project', 'role', 'stack']

conn = boto.ec2.connect_to_region(cli_args.aws_region,
                                  aws_access_key_id=cli_args.aws_access_key_id,
                                  aws_secret_access_key=cli_args.aws_secret_access_key)

reservations = conn.get_all_instances()

for reservation in reservations:
    for instance in reservation.instances:
        if instance.tags['project'] in cli_args.project_name:
            volumes = conn.get_all_volumes(filters={'attachment.instance-id': instance.id})

            for volume in volumes:
                for tag in tags_to_sync:
                    volume.add_tag(tag, instance.tags[tag])
                    print "added %s=%s to %s" % (tag, instance.tags[tag], volume.id)