import boto3

# Find the region of a specific instance
def find_instance_region(instance_id):
    ec2_client = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    for region in regions:
        try:
            ec2 = boto3.client('ec2', region_name=region)
            response = ec2.describe_instances(InstanceIds=[instance_id])
            reservations = response['Reservations']
            if reservations:
                return region
        except Exception:
            pass

    return None

