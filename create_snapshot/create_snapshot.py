#!/usr/bin/python
import boto.ec2
import argparse
import sys

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

parser.add_argument('-name', action='store',
                    dest='instance_name',
                    help='instance name (Name tag value)',
                    required=True)

parser.add_argument('-keep', action='store',
                    dest='snapshots_to_keep',
                    help='qty of snapshots to keep',
                    default='15',
                    type=int)

cli_args = parser.parse_args()

conn = boto.ec2.connect_to_region(cli_args.aws_region,
                                  aws_access_key_id=cli_args.aws_access_key_id,
                                  aws_secret_access_key=cli_args.aws_secret_access_key)

reservations = conn.get_all_instances(filters={'tag:Name': cli_args.instance_name})

for reservation in reservations:
    for instance in reservation.instances:
        volumes = conn.get_all_volumes(filters={'attachment.instance-id': instance.id})

        for volume in volumes:
            new_snapshot = conn.create_snapshot(volume.id, "snapshot for %s - %s" % (instance.tags.get('Name')), volume.id)
            available_snapshots = conn.get_all_snapshots(filters={'volume-id': volume.id})
            snapshot_array = []

            for existent_snapshot in available_snapshots:
                snapshot_array.append(existent_snapshot)

            for snapshot_to_delete in sorted(snapshot_array, key=lambda k: k.start_time, reverse=True)[
                                      cli_args.snapshots_to_keep:]:
                snapshot_to_delete.delete()
                print "snapshot %s with start time %s deleted" % (snapshot_to_delete, snapshot_to_delete.start_time)
