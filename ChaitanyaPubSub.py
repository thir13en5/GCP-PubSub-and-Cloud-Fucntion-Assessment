import base64
import json
import argparse
import os
import time
import googleapiclient.discovery
from six.moves import input

def hello_pubsub(event, context):
	#decoding the base64 encoded data recieved from pub/sub published message
    pubsub_message = base64.b64decode(event["data"]).decode('utf-8')
	#parsing the string containing json into actual json
	#configuring all the variables fromt the json data published by pub/sub
    msg_json = json.loads(pubsub_message) 
    zone = msg_json["zone"]
    name = msg_json["name"]
    bucket_from = msg_json["bucket_from"]
    bucket_to = msg_json["bucket_to"]
    project = msg_json["project"]
    #debugging messages
    print(zone)
    print(name)
    print(bucket_from)
    print(bucket_to)
    print(project) 
    instance_name = name
    # [START create_instance]
    def create_instance(compute, project, zone, name):
        # Get the latest Debian Jessie image.
        image_response = compute.images().getFromFamily(
            project='debian-cloud', family='debian-8').execute()
        source_disk_image = image_response['selfLink']
        # Configure the machine
        machine_type = "zones/%s/machineTypes/n1-standard-1" % zone
        config = {
            'name': name,
            'machineType': machine_type,
            # Specify the boot disk and the image to use as a source.
            'disks': [
                {
                    'boot': True,
                    'autoDelete': True,
                    'initializeParams': {
                        'sourceImage': source_disk_image,
                    }
                }
            ],
            # Specify a network interface with NAT to access the public
            # internet.
            'networkInterfaces': [{
                'network': 'global/networks/default',
                'accessConfigs': [
                    {'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
                ]
            }],
            # Allow the instance to access cloud storage and logging.
            'serviceAccounts': [{
                'email': 'default',
                'scopes': [
                    'https://www.googleapis.com/auth/devstorage.read_write',
                    'https://www.googleapis.com/auth/logging.write'
                ]
            }],
            # Metadata is readable from the instance and allows you to
            # pass configuration from deployment scripts to instances.
            'metadata': {
                'items': [{
                    	'key': 'BucketFrom',
                    	'value': bucket_from
            		}, {
						'key': 'BucketTo',
                  		'value': bucket_to
            		}, {
                		# Startup script is automatically executed by the
                		# instance upon startup.
						#hardcoded the bucket names can alter with above defined keys
                		'key': 'startup-script',
                		'value': "#!/bin/bash\ngsutil cp gs://chaitanya-bucket-from/invoker.jfif gs://chaitanya-bucket-to/\n"
            	}]
            }
        }
        return compute.instances().insert(
            project=project,
            zone=zone,
            body=config).execute()
    # [END create_instance]
    # [START delete_instance]
    def delete_instance(compute, project, zone, name):
        return compute.instances().delete(
            project=project,
            zone=zone,
            instance=name).execute()
    # [END delete_instance]
    # [START wait_for_operation]
    def wait_for_operation(compute, project, zone, operation):
        print('Waiting for operation to finish...')
        while True:
            result = compute.zoneOperations().get(
                project=project,
                zone=zone,
                operation=operation).execute()
            if result['status'] == 'DONE':
                print("done.")
                if 'error' in result:
                    raise Exception(result['error'])
                return result
            time.sleep(1)
    # [END wait_for_operation]
    # [START run]
    def main(project, zone, instance_name):
        compute = googleapiclient.discovery.build('compute', 'v1')
        print('Creating instance.')
        operation = create_instance(compute, project, zone, instance_name)
        wait_for_operation(compute, project, zone, operation['name'])
        print('Instances in project %s and zone %s:' % (project, zone))
        print("Instance created.It will take a minute or two for the instance to complete work.")
        print("File copied from bucket1 to bucket2....")
        print('Deleting instance.')
        operation = delete_instance(compute, project, zone, instance_name)
        print('Instance Deleted')
    main(project, zone, instance_name)
    # [END run] 