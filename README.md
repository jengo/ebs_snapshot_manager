# Warning, this script is in development and is not currently recommended for use!

### EBS Snapshot Manager

Simple Python script that can create and rotate EBS snapshots.


### Installation

pip install boto

Create a config file in /etc/ebs_snapshot_manager.cfg with the following contents

```
[credentials]
accessKey=AWS_ACCESS_KEY
secretKey=AWS_SECRET_KEY
regions=us-west-1

[snapshot]
volumes=ALL
instances=ALL
totalToKeep=3
```

The config file should NOT be world as it contains credentials.  It is recommended that you create a separate user to run this script, not root or the same user as your webserver.

AWS permissions required: ec2:CreateSnapshot, ec2:DeleteSnapshot, ec2:DescribeInstances, ec2:DescribeSnapshots, ec2:DescribeVolumes, ec2:CreateTags

Add a cron entry for how often you would like the snapshots to be generated.  EBS snapshots can get expensive so keep that in mind on how often you choose to run it.

Example of my setup:

/etc/cron.d/ebs_snapshot_manager

```
20 */2 * * * snapshots /usr/local/bin/ebs_snapshot_manager.py >> /var/log/ebs_snapshot_manager.log 2>&1
```


