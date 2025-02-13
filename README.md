Before start application install pm2 and requirements 
#################

install pm2 as per OS

cd /path/to/files
python3 -m pip install -r requirements.txt


#need to configure aws or attach before start  

To start app run 
-----------------

 pm2 start app.py --name slack-API-sanbox --interpreter=python3
 pm2 start worker.py --name worker --interpreter=python3

> 5000 port open in security group
>
> aws configure just add any region and output ( no access key and secret key if role attached else add both)

Usage
------
To add an instance ID to the temporary ignore list: /ignore_instance add <instance_id>

To remove an instance ID from the temporary ignore list: /ignore_instance remove <instance_id>

To add an instance ID to the permanent ignore list: /ignore_instance add_permanent <instance_id>

To remove an instance ID from the permanent ignore list: /ignore_instance remove_permanent <instance_id>

To stop an instance  /ignore_instance stop <instance_id>

