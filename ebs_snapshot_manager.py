#!/usr/bin/env python

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Written by Jo Engo <dev.toaster@gmail.com>

__version__ = '1.2'

import boto
import boto.ec2

import argparse
import os, sys

try:
	# Python 3
	import configparser
except ImportError:
	# Python 2
	import ConfigParser as configparser

parser = argparse.ArgumentParser(description='EBS Snapshot Manager %s' % __version__)
parser.add_argument('-c', '--config', help='Config file', required=False, default="/etc/ebs_snapshot_manager.cfg")
parser.add_argument('-d', '--dryrun', help='Dry run', required=False, default=False, action='store_true')
parser.add_argument('-a', '--attachedOnly', help='Create snapshots of only volumes attached to an instance', required=False, default=False, action='store_true')
parser.add_argument('-T', '--skipTagging', help='Do not add tags to snapshots (includes information like instance id and mount device)', required=False, default=False, action='store_true')
parser.add_argument('--version', action='version', version='EBS Snapshot Manager %s' % __version__)
args   = parser.parse_args()

config = configparser.ConfigParser()


try:
	config.readfp(open(args.config))
except:
	print("Could not open config file {0}".format(args.config))
	sys.exit()


try:
	totalToKeep = config.getint('snapshot', 'totalToKeep')
except:
	print("Invalid totalToKeep setting")
	sys.exit()


# Arguments have priority over config
if not args.attachedOnly:
	try:
		if config.getboolean('snapshot', 'attachedOnly'):
			args.attachedOnly = True

	except:
		pass

if not args.skipTagging:
	try:
		if config.getboolean('snapshot', 'skipTagging'):
			args.skipTagging = True

	except:
		pass


for region in config.get('credentials', 'regions').split(','):
	conn = boto.ec2.connect_to_region(region,
		aws_access_key_id=config.get('credentials', 'accessKey'),
		aws_secret_access_key=config.get('credentials', 'secretKey'))


	volumes = []
	filters = {}

	# Note:  This does support mixing and matching instances and volume filters
	# However, there is currently no error reporting when you specify an impossible condition
	# For example:  Filtering a volume and instance that aren't attached together
	if config.get('snapshot', 'instances') != "ALL":
		filters = {
			"attachment.instance-id": config.get('snapshot', 'instances').split(',')
		}


	# Get list of volumes or the list of volumes in the config
	if config.get('snapshot', 'volumes') == "ALL":
		for volume in conn.get_all_volumes(filters=filters):
			volumes.append(volume)
	else:
		volume_ids = config.get('snapshot', 'volumes').split(',')

		for volume in conn.get_all_volumes(volume_ids, filters=filters):
			volumes.append(volume)

	# Build the snapshots for each volume
	for volume in volumes:
		if args.attachedOnly and volume.attachment_state() != "attached":
			print("Volume {0} isn't attached, skipping".format(volume.id))
			continue

		snapshots = conn.get_all_snapshots(owner='self', filters={'volume_id': volume.id})


		# Create snapshot first
		if args.dryrun == False:
			snapshot = conn.create_snapshot(volume.id)
			print("Creating snapshot for volume {0} snapshot {1} on instance {2} with device {3}".format(volume.id, snapshot.id,
				volume.attach_data.instance_id, volume.attach_data.device))

			# Tag the snapshot
			if not args.skipTagging and volume.attachment_state() == "attached":
				tags = {
					"instance-id": volume.attach_data.instance_id,
					"device": volume.attach_data.device
				}

				conn.create_tags(snapshot.id, tags)

		else:
			print("Creating snapshot for volume {0} on instance {1} with device {2}".format(volume.id, volume.attach_data.instance_id,
				volume.attach_data.device))



		# Now find snapshots to remove
		for snapshot in sorted(snapshots, key=lambda x: x.start_time, reverse=True)[totalToKeep - 1:]:
			if args.dryrun == False:
				conn.delete_snapshot(snapshot.id)

			print("Deleting snapshot {0} for volume {1} which was created on {2}".format(snapshot.id, snapshot.volume_id,
				snapshot.start_time))



