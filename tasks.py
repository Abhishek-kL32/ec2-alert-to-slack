import boto3
import mysql.connector
import requests
from datetime import datetime, timedelta
import redis
import json

# Redis configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# Slack webhook URL
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"

# Email-to-Slack mapping
EMAIL_TO_SLACK_ID = {
    "abhishek.krishna@epiuse.com": "U071QJKRA4X",
    "abin.joseph@epiuse.com": "U02HCMCSNQG",
    "adarsh.k@epiuse.com": "U01GZNA6VGQ",
    "adhilekshmi.ps@epiuse.com": "U058X419M2Q",
    "Angel.Varghese@epiuse.com": "U0702BVUCR2",
    "anoop.rajeev@epiuse.com": "U02MAG5AF3M",
    "anusree.o@epiuse.com": "U02G8B6KT5M",
    "arjun.dev@epiuse.com": "UB1TNSUP5",
    "catherine.anto@epiuse.com": "U04DAGVNX0T",
    "denny.antony@epiuse.com": "U06H9E7EQ2Y",
    "devika.sreenivasan@epiuse.com": "U06HKL33PCH",
    "julious.gonsalves@epiuse.com": "U040144G2N4",
    "kavya.k@epiuse.com": "U05QLF24ZHQ",
    "megha.chithran@epiuse.com": "U02HCMCMFKJ",
    "nandhu.krishnan@epiuse.com": "U04DAGW7GLT",
    "sajni.v@epiuse.com": "U071J0S9G15",
    "saradha.seenivasan@epiuse.com": "U06HVPVUG0Y",
    "sherry.john@epiuse.com": "U04MR9CL2JK",
    "shine.kumar@epiuse.com": "U01FE9NJGQP",
    "shyam.prakash@epiuse.com": "U01GA3LAHC3",
    "sourav.k@epiuse.com": "U06GSDYQG4F",
    "Sreelakshmi.Km@epiuse.com": "U04D7MKMU85",
    "suraj.krishnan@epiuse.com": "U04E0B751CY",
    "visakh.kk@epiuse.com": "U01RX8N2KAL",
    "visakh.us@epiuse.com": "U01G0GUQMLY",
    "vishnu.cp@epiuse.com": "U058RLQB493",
    "surya.krishna@epiuse.com": "U01N2BTD78F",
    "rahul.nampoothiri@epiuse.com": "U07CHQHE3S8",
    "alvin.varghese@epiuse.com": "U07CF70CTGT",
    "swathi.rajendran@epiuse.com": "U07CF70PC9H",
    "sharmila.chandru@epiuse.com": "U07D4451PU0",
    "luis.cassares@epiuse.com": "U03RXLQSPHA",
    "joshua.brown@epiuse.com": "U04DF228FQD",
    "elson.ealias@epiuse.com": "U07RTHY9R2Q",
    "amal.das@epiuse.com": "U07SDSL9CP2",
    "stinoy.stanley@epiuse.com": "U07QP326VU6",
    "bency.benny@epiuse.com": "U07RJF75FUG",
    "joshua.tymorek@epiuse.com": "U07B09KD4A3",
    "alikha.krishna@epiuse.com": "U07FKV4EM6Y",
    "aswani.chandran@epiuse.com": "U07K8Q5TW8P",
    "ward.townsend@epiuse.com": "U01GF5XMSUV",
}

# MySQL Database Configuration
DB_CONFIG = {
    'user': 'slack_user',
    'password': 'T33th123!',
    'host': 'localhost',
    'database': 'slack_ignore_db'
}
def start_instance(instance_id):
    """
    Locate and start an EC2 instance across all regions.
    """
    try:
        print(f"Attempting to start instance {instance_id}")

        # Create a general EC2 client to list regions
        ec2_client = boto3.client('ec2')
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

        found = False
        for region in regions:
            try:
                # Connect to EC2 in the current region
                ec2_client = boto3.client('ec2', region_name=region)
                response = ec2_client.describe_instances(InstanceIds=[instance_id])

                # Check if the instance exists in this region
                reservations = response.get('Reservations', [])
                if reservations:
                    # Extract the region from the instance's placement
                    region = reservations[0]['Instances'][0]['Placement']['AvailabilityZone'][:-1]
                    print(f"Instance {instance_id} is in region {region}")
                    found = True
                    break
            except Exception as e:
                # Catch exceptions where the instance isn't found in the current region
                print(f"Error checking region {region}: {str(e)}")

        if not found:
            raise ValueError(f"No running instance found with ID {instance_id} in any region")

        # Connect to the specific region where the instance is located
        ec2_client = boto3.client('ec2', region_name=region)
        start_response = ec2_client.start_instances(InstanceIds=[instance_id])
        print(f"Start response: {start_response}")

        return {
            'statusCode': 200,
            'body': json.dumps(f"Instance {instance_id} in region {region} is starting.")
        }

    except Exception as e:
        print(f"Error starting instance {instance_id}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error starting instance {instance_id}: {str(e)}")
        }

def stop_instance(instance_id):
    try:
        print(f"Attempting to stop instance {instance_id}")

        ec2_client = boto3.client('ec2')
        regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

        found = False
        for region in regions:
            try:
                ec2_client = boto3.client('ec2', region_name=region)
                response = ec2_client.describe_instances(InstanceIds=[instance_id])
                reservations = response['Reservations']
                if reservations:
                    region = reservations[0]['Instances'][0]['Placement']['AvailabilityZone'][:-1]
                    print(f"Instance {instance_id} is in region {region}")
                    found = True
                    break
            except Exception as e:
                print(f"Error checking region {region}: {str(e)}")

        if not found:
            raise ValueError(f"No running instance found with ID {instance_id} in any region")

        ec2_client = boto3.client('ec2', region_name=region)
        stop_response = ec2_client.stop_instances(InstanceIds=[instance_id])
        print(f"Stop response: {stop_response}")

        return {
            'statusCode': 200,
            'body': json.dumps(f"Instance {instance_id} in region {region} is stopping.")
        }

    except Exception as e:
        print(f"Error stopping instance {instance_id}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Error stopping instance {instance_id}: {str(e)}")
        }
## Cleanup temporary ignore list

def cleanup_ignore_list(days=7):
    """
    Remove entries from the temporary ignore list older than 'days'.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        query = 'DELETE FROM ignore_list WHERE timestamp < NOW() - INTERVAL %s DAY'
        cursor.execute(query, (days,))
        conn.commit()
        print(f"Removed entries older than {days} days from the ignore list.")
    except Exception as e:
        print(f"Error during ignore list cleanup: {e}")
    finally:
        conn.close()

### Ignore List Management ###

def add_to_ignore_list(instance_id):
    """Add an instance to the temporary ignore list."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO ignore_list (instance_id) VALUES (%s) ON DUPLICATE KEY UPDATE timestamp = CURRENT_TIMESTAMP',
            (instance_id,)
        )
        conn.commit()
        print(f"Instance {instance_id} added to temporary ignore list.")
    except Exception as e:
        print(f"Error adding instance {instance_id} to ignore list: {e}")
    finally:
        conn.close()

def remove_from_ignore_list(instance_id):
    """Remove an instance from the temporary ignore list."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ignore_list WHERE instance_id = %s', (instance_id,))
        conn.commit()
        print(f"Instance {instance_id} removed from temporary ignore list.")
    except Exception as e:
        print(f"Error removing instance {instance_id} from ignore list: {e}")
    finally:
        conn.close()

def fetch_ignore_list():
    """Fetch the list of instances to temporarily ignore."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('SELECT instance_id FROM ignore_list')
        ignore_list = {row[0] for row in cursor.fetchall()}
        return ignore_list
    except Exception as e:
        print(f"Error fetching temporary ignore list: {e}")
        return set()
    finally:
        conn.close()

def fetch_permanent_ignore_list():
    """Fetch the list of instances to permanently ignore."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('SELECT instance_id FROM permanent_ignore_list')
        permanent_ignore_list = {row[0] for row in cursor.fetchall()}
        return permanent_ignore_list
    except Exception as e:
        print(f"Error fetching permanent ignore list: {e}")
        return set()
    finally:
        conn.close()

def add_to_permanent_ignore_list(instance_id):
    """Add an instance to the permanent ignore list."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO permanent_ignore_list (instance_id) VALUES (%s)',
            (instance_id,)
        )
        conn.commit()
        print(f"Instance {instance_id} added to permanent ignore list.")
    except Exception as e:
        print(f"Error adding instance {instance_id} to permanent ignore list: {e}")
    finally:
        conn.close()

def remove_from_permanent_ignore_list(instance_id):
    """Remove an instance from the permanent ignore list."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM permanent_ignore_list WHERE instance_id = %s', (instance_id,))
        conn.commit()
        print(f"Instance {instance_id} removed from permanent ignore list.")
    except Exception as e:
        print(f"Error removing instance {instance_id} from permanent ignore list: {e}")
    finally:
        conn.close()

# Send a Slack notification
def send_slack_notification(message):
    """Send a message to Slack."""
    try:
        payload = {"text": message}
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Slack notification sent successfully")
    except Exception as e:
        print(f"Error sending Slack notification: {e}")

# Notify about a specific instance
def notify_instance(instance, instance_name, running_time, region):
    """Notify about an instance running for a multiple of 10 hours."""
    instance_id = instance['InstanceId']
    launch_time = instance['LaunchTime'].strftime("%Y-%m-%d %H:%M:%S")
    email, role_name = find_user_email(instance_id, region)

    slack_user_id = EMAIL_TO_SLACK_ID.get(email)
    mention = f"<@{slack_user_id}>" if slack_user_id else "<!channel>"

    message = (
        f"{mention}\n"
        f"The EC2 instance '{instance_name}' and ID : {instance_id} in region {region} has been running for {running_time:.2f} hours.\n"
        f"Launched by: {email or role_name or 'Unknown'} at {launch_time}\n"
        "Please stop or terminate it if it is no longer required."
    )
    send_slack_notification(message)

# Find the email of the user who launched the instance
def find_user_email(instance_id, region):
    """Retrieve the user email or role name who launched the instance using CloudTrail."""
    try:
        cloudtrail_client = boto3.client('cloudtrail', region_name=region)
        start_time = datetime.utcnow() - timedelta(days=90)
        end_time = datetime.utcnow()

        next_token = None

        while True:
            # Lookup CloudTrail events with pagination
            if next_token:
                events_response = cloudtrail_client.lookup_events(
                    LookupAttributes=[{'AttributeKey': 'ResourceName', 'AttributeValue': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    MaxResults=50,  # Fetch more events per page
                    NextToken=next_token
                )
            else:
                events_response = cloudtrail_client.lookup_events(
                    LookupAttributes=[{'AttributeKey': 'ResourceName', 'AttributeValue': instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    MaxResults=50
                )

            for event in events_response['Events']:
                event_data = json.loads(event['CloudTrailEvent'])
                print(f"Processing event: {event_data.get('eventName')} for instance {instance_id}")

                # Check for relevant events
                if event_data.get('eventName') in ['RunInstances', 'StartInstances']:
                    user_identity = event_data.get('userIdentity', {})
                    principal_id = user_identity.get('principalId', '')
                    role_name = user_identity.get('arn', '').split('/')[-1]

                    if ':' in principal_id:
                        email = principal_id.split(':')[1]
                        print(f"Extracted email: {email}, Role: {role_name}")
                        return email, role_name

            # Check for pagination
            next_token = events_response.get('NextToken')
            if not next_token:
                break  # Exit loop if no more pages

        # Fallback if no matching events are found
        print("No matching CloudTrail event with email found")
        return "Unknown", "Unknown"
    except Exception as e:
        print(f"Error retrieving user email: {e}")
        return "Unknown", "Unknown"

# Fetch EC2 instances and monitor uptime
def fetch_ec2_instances():
    """Fetch running instances and check their uptime."""
    ignore_list = fetch_ignore_list()
    permanent_ignore_list = fetch_permanent_ignore_list()
    combined_ignore_list = ignore_list.union(permanent_ignore_list)  # Combine both sets

    ec2_client = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    for region in regions:
        ec2 = boto3.client('ec2', region_name=region)
        paginator = ec2.get_paginator('describe_instances')
        response_iterator = paginator.paginate(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

        for page in response_iterator:
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    if instance_id in combined_ignore_list:
                        continue

                    # Extract instance name tag
                    instance_name = "Unknown"
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'Name':
                                instance_name = tag['Value']
                                break

                    launch_time = instance['LaunchTime']
                    current_time = datetime.utcnow()
                    running_time = (current_time - launch_time.replace(tzinfo=None)).total_seconds() / 3600

                    # Check if running time is a multiple of 10
                    if int(running_time) % 10 == 0 and int(running_time) >= 10:
                        redis_key = f'alerted_{instance_id}_{int(running_time)}'
                        if not redis_client.get(redis_key):  # Avoid duplicate alerts for the same multiple
                            notify_instance(instance, instance_name, running_time, region)
                            redis_client.setex(redis_key, 3600 * 10, 'alerted')  # Expire after 10 hours

