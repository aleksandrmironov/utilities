#Script to backup EBS volumes


usage:
 ```
create_snapshot.py [-h]
-id AWS_ACCESS_KEY_ID(required)
-key AWS_SECRET_ACCESS_KEY(required)
-region AWS_REGION(default eu-west-1)
-name INSTANCE_NAME (tag Name value)
-keep SNAPSHOTS_TO_KEEP (15 defaults)
```