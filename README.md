<h1 align = "center">Bulk Provisioning of Video Mesh Nodes and Day 2 Support</h1>

<br />

* [Bulk Provisioning of Video Mesh Nodes](#bulk-provisioning)
* [Changing the Admin Account Password of Nodes in Bulk](#password)
* [External Network Configuration](#dual-ip)


<br />

---

<br />

## <a id="bulk-provisioning"></a> **Bulk Provisioning of Video Mesh Nodes**  

<br />

Video Mesh customers with many Video Mesh deployments find manual provisioning of the nodes time-consuming.  

The bulk provisioning script enables your administrators to run automatic deployment of Video Mesh nodes on VMWare ESXi servers.  

The script uses the ovftool API to manage machines on ESXi, bringing up VMNs by multiprocessing. Your administrator can assign network parameters (IP, netmask, Gateway, DNS, NTP, Hostname) to the VMN as part of running the script.  

The script supports deployment of VMNs on standalone ESXi hosts and vCenter-managed ESXi hosts.


**Versioning information**


Please refer to the wiki: https://github.com/CiscoDevNet/webex-video-mesh-node-provisioning/wiki

<br />

### **Pre-requisites:**  
* OVA File - The Video Mesh OVA file that helps in deployment of VMN. Place this file in the same directory as the script.
* config.json - This file contains the common configurations such as ovf_filename (path), and the internal and external network settings.
* Input Data - There are 2 csv files depending on how the ESXi is managed -
    1.	`input_data.csv`: For the deployment on standalone ESXi host.  
    2.	`input_data_vcenter.csv`: For the deployment on ESXi host managed by vCenter.   

    Note: Edit the appropriate csv file to include all details of the nodes to deploy. Refer to the [sample csv](#sample-csv) attached below for more details.


* Ovftool - You must install this API to deploy and manage Machines on ESXi servers. 
    1.	Download the ovftool for Linux or MacOS -> (https://developer.vmware.com/web/tool/4.4.0/ovf)
    2.	Create a virtual environment (venv) and activate it -> (https://docs.python.org/3/library/venv.html)
    3.	Install the ‘pip’ module
    4.	Install ovftool:  
        *	For Linux, follow this procedure:  
            * Unzip the OVF Tool
            * Add the following line to your ~/.bashrc file:   
                `export PATH=$PATH:<downloaded path>/ovftool`
            * Run the .bashrc file:
                > source ~/.bashrc  
        *	For MacOS, follow this procedure:  
            * Install the ovftool through the usual application installation.  
            * Move all the files present in `Applications/VMWare OVF Tool` to the venv’s `bin` directory.  
            * Re-activate the venv.  
    5.	Install the modules:  
        >   pip install -r requirements.txt


<br />

### <a id="sample-csv"></a> **Sample csv:** 

<br />

**<u>For standalone ESXi hosts -</u>**

| esxi\_host   | username | password | datastore\_name        | name      | ip          | mask          | gateway    | dns            | ntp         | hostname | esxi\_internal\_nw | esxi\_external\_nw | deployment\_option |
| ------------ | -------- | -------- | ---------------------- | --------- | ----------- | ------------- | ---------- | -------------- | ----------- | -------- | ------------------ | ------------------ | ------------------ |
| 1.1.1.1 | user     | passwd   | datastore1 | test\_vm3 | 3.3.3.3 | 5.5.5.5 | 6.6.6.6 |     7.7.7.7\|7\.7.7.8\|7.7.7.9 | 8.8.8.8 | user1    | VM Network         | VM Network         | CMS1000            |
| 2.2.2.2 | user     | passwd   | datastore2 | test\_vm4 | 4.4.4.4 | 5.5.5.5 | 6.6.6.6 |      7.7.7.7 | 8.8.8.8\|8.8.8.9 | user2.domain.com    | VM Network         | VM Network         | VMNLite            |

<br />

* esxi_host - ESXi Host IP
* username - ESXi Host Username
* password - ESXi Host Password
* datastore_name - Datastore name on which to deploy the VMN (can be found on the ESXi server under 'Storage')
* name- VM Name
* ip - Static IP address of the VM
* mask - Netmask
* gateway - Gateway
* dns - One or more DNS servers. You can include multiple DNS servers in a pipe-delimited ( | ) list. Only IP format is accepted.
* ntp - One or more NTP servers. You can include multiple NTP servers in a pipe-delimited ( | ) list. Also takes FQDN as input.
* hostname - Host name of the VM. You can include the domain as hostname.domain.com
* esxi_internal_nw - ESXI Internal Network (can be found on the ESXi server under 'Networking')
* esxi_external_nw - ESXI External Network (can be found on the ESXi server under 'Networking')
* deployment_option - Deployment Type ('VMNLite' or 'CMS1000') 

<br />
<br />

**<u>For ESXi hosts managed by vCenter servers -</u>**

<br />

| vcenter | username | password | datastore\_name | name      | ip      | mask    | gateway | dns                     | ntp             | hostname         | esxi\_internal\_nw | esxi\_external\_nw | deployment\_option | esxi             |
|---------| -------- | -------- | --------------- | --------- | ------- | ------- | ------- | ----------------------- | --------------- | ---------------- | ------------------ | ------------------ | ------------------ |------------------|
| 1.1.1.1 | user     | passwd   | datastore1      | test\_vm3 | 3.3.3.3 | 5.5.5.5 | 6.6.6.6 | 7.7.7.7\|7.7.7.8\|7.7.7.9 | 8.8.8.8         | user1            | VM Network         | VM Network       | CMS1000           | 1.2.3.4 |
| 2.2.2.2 | user     | passwd   | datastore2      | test\_vm4 | 4.4.4.4 | 5.5.5.5 | 6.6.6.6 | 7.7.7.7                 | 8.8.8.8\|8.8.8.9 | user2.domain.com | VM Network         | VM Network         | VMNLite          | 5.6.7.8 |

<br />

* vcenter - vCenter server IP
* username - vCenter Username
* password - vCenter Password
* datastore_name - Datastore name on which to deploy the VMN (can be found on the ESXi server under 'Storage')
* name- VM Name
* ip - Static IP address of the VM
* mask - Netmask
* gateway - Gateway
* dns - One or more DNS servers. You can include multiple DNS servers in a pipe-delimited ( | ) list. Only IP format is accepted.
* ntp - One or more NTP servers. You can include multiple NTP servers in a pipe-delimited ( | ) list. Also takes FQDN as input.
* hostname - Host name of the VM. You can include the domain as hostname.domain.com
* esxi_internal_nw - ESXI Internal Network (can be found on the ESXi server under 'Networking')
* esxi_external_nw - ESXI External Network (can be found on the ESXi server under 'Networking')
* deployment_option - Deployment Type ('VMNLite' or 'CMS1000')
* esxi - The exact ESXi name/IP present in the vcenter on which VMN needs to be deployed.
<br />


### **Running the script to bulk provision VMN:** 

> git clone https://github.com/CiscoDevNet/webex-video-mesh-node-provisioning.git 

> cd webex-video-mesh-node-provisioning

> pip install -r requirements.txt

> Edit the input_data.csv/input_data_vcenter.csv to include details

> python3 runner.py -m [arg]  

(arg is either 'standalone' or 'vcenter', depending on the whether the ESXi is managed by vCenter or not)

<br />

### **Error messages:**

If there is invalid input in the `input_data.csv`/`input_data_vcenter.csv`, the script doesn’t start to deploy the Video Mesh nodes. The script returns a message stating what the invalid input was. Re-run the script after correcting the invalid input. Errors that can stop the script include:
* Incorrect credentials
* Blank or invalid IP, DNS, NTP, etc.
* Duplicate VM names
* Duplicate Ips
* The OVF isn’t present in the same directory.    

If problems occur during the deployment of the VMNs, the script displays this information:
* Nodes with incorrect datastore or internal/external network appear first, and they aren't included in the progress indicator at all.
* Nodes that couldn’t deploy due to insufficient ESXi resources show 0% configuration progress.
* Summary of Nodes that successfully deployed, and Nodes that failed (with appropriate reason for failure).


Some screenshots for error messages are added in this wiki: https://github.com/CiscoDevNet/webex-video-mesh-node-provisioning/wiki/Sample-Error-Messages-for-Bulk-Provisioning-of-VMNs

<br />


### **Troubleshooting:**

When the script completes running, it generates two types of log files. One log file, “vmn_provisioning.log”, contains logs of the entire process. The other type of log file, “ovf_<VMN_IP>.log”, is specific to each VMN deployment, where VMN_IP corresponds to the IP address of each VMN. You can investigate these logs upon further failures of the deployment.  

The Password in the csv is masked by ***** for every row whose deployment is successful, and by ##### for every row whose deployment failed. Enter the password again for the failed rows if the script is re-run. Do not share the original csv file with anyone as it contains password as plaintext.

 _Check that all the nodes from the CSV file deployed correctly. If some nodes did not deploy, edit the CSV file to provide the necessary information and run the script again._

<br />

---

<br />

## <a id="password"></a> **Changing the Admin Account Password of Nodes in Bulk**

<br />

Once you deploy the nodes, the Admin account password of the nodes need to be changed, before proceeding to use the node.

This script allows you to change the admin user's password in bulk. You can use this script to change the admin password immediately after the VMN deployment or at any other point.

Edit the `input_password.csv` file to include details of the nodes for which to change the admin account password  (VMN IP/FQDN, Old Password, New Password).

Leave the Old Password field blank if you’re changing the password for that node for the first time ever (recently deployed nodes).

<br />

### **Sample csv:**

| video\_mesh\_node | old\_password | new\_password |
|-------------------| ------------- | ------------- |
| 1.1.1.1           |               | newpass       |
| hostname.domain    |               | newpass       |
| 2.2.2.2           | oldpass       | newpass       |

<br />

* video_mesh_node - The IP/FQDN of the Video Mesh Node for which to change the admin password
* old_password - The old password of the node (leave blank if first time set-up)
* new_password - The new password of the node

<br />

### **Running the script to change Admin Account Password:**

> git clone https://github.com/CiscoDevNet/webex-video-mesh-node-provisioning.git 

> cd webex-video-mesh-node-provisioning

> pip install -r requirements.txt

> Edit the input_password.csv to include details

> python3 change_password.py

<br />

The script displays the nodes for which the password change failed first (with the reason for failure), followed by the nodes for which the password change was successful.  

The Password in the csv is masked by ***** for every row whose password change was successful, and by ##### for every row whose password change failed. Enter the password again for the failed rows if the script is re-run. Do not share the original csv file with anyone as it contains password as plaintext.

Constraints for new password:
* Cannot be same as previous 3 passwords  
* 8 - 40 characters accepted  
* Should be a non-dictionary word  
* Should contain at least 3 of these character types: uppercase letters, lowercase letters, numbers, and special characters

<br />

---

<br />

## <a id="dual-ip"></a> **External Network Configuration**

<br />

**NOTE: You can only do this configuration for newly deployed Video Mesh Nodes, whose default admin password has changed. Don’t use this script after registering the node to an organisation.**

You can use this script to add the external IP to your Video Mesh nodes.

Edit the `input_external_nw.csv` file to include details of the nodes for which to set up the external network (Node IP/FQDN, Username, Password, External IP, External Netmask, External Gateway).

<br />

### **Sample csv:**

| video\_mesh\_node | username | password | ext\_ip | ext\_mask | ext\_gw |
| -------- | -------- | -------- | ------- | --------- | ------- |
| 1.1.1.1  | admin    | passwd   | 1.2.3.4 | 2.3.4.5   | 3.3.3.3 |
| hostname.domain  | admin    | passwd   | 5.6.7.8 | 6.7.8.9   | 4.4.4.4 |

<br />

* video_mesh_node - The IP/FQDN of the Video Mesh Node to add the External IP details
* username - The username of the node
* password - The password of the node
* ext_ip - The External IP to add
* ext_mask - The Netmask for the External Network
* ext_gw - The Gateway for the External Network

<br />

### **Running the script to enable and edit External Network Configuration:**

> git clone https://github.com/CiscoDevNet/webex-video-mesh-node-provisioning.git 

> cd webex-video-mesh-node-provisioning

> pip install -r requirements.txt

> Edit the input_external_nw.csv to include details

> python3 external_network.py

<br />

The script displays the summary of the external network configuration (whether successful or failed) after running.

The Password in the csv is masked by ***** for every row whose external network change is successful, and by ##### for every row whose external network change failed. Enter the password again for the failed rows if the script is re-run. Do not share the original csv file with anyone as it contains password as plaintext.


<br />

---

<br />
