<h1 align = "center">Bulk Provisioning of Video Mesh Nodes </h1>

## **Introduction**  
Video mesh customers with substantial number of Video Mesh deployments are finding it difficult to expand as manual provisioning of the nodes are time-consuming.  


The script will help customer admin to run automatic deployment of Video Mesh Nodes on the VMWare ESXi servers.   


The script uses the ovftool API to manage machines on the ESXi, in such a way that VMNs are brought up by multiprocessing. It enables the administrator to assign network parameters (IP, netmask, Gateway, DNS, NTP, Hostname) to the VMN as part of running the script.


<br />

## **Pre-requisites**  
* OVA File - The Video Mesh OVA file that helps in deployment of VMN. Place this file in the same directory as the script.
* config.json - This file contains the common configurations such as ovf_filename (path), and the internal and external network settings.
* input_data.csv - This CSV file takes the ESXi server IP and Credentials, Datastore, VM Name, Network configs (IP, netmask, Gateway, 1 DNS [only IP format], 1 NTP [also takes FQDN as input], Hostname [or FQDN]), and the Deployment Type ('VMNLite' or 'CMS1000') as input. Edit this csv file to include all details of nodes to be deployed.


* Ovftool is the API used to deploy and manage Machines on ESXi servers. This needs to be installed. 
    1.	Download the ovftool for Linux or MacOS -> (https://developer.vmware.com/web/tool/4.4.0/ovf)
    2.	Create a virtual environment (venv) and activate it -> (https://docs.python.org/3/library/venv.html)
    3.	Install the ‘pip’ module
    4.	Install ovftool:  
        *	For Linux, follow this procedure:  
            * Unzip the OVF Tool
            * Add the following line to your .bashrc file:   
                `export PATH=$PATH:<downloaded path>/ovftool`
            * Run the .bashrc file:
                > source .bashrc  
            * Run the following command:
                > chmod +x ovftool; sync; ovftool --eulas-agreed --console –required
        *	For MacOS, follow this procedure:  
            * Install the ovftool through the usual application installation.  
            * Move all the files present in `Applications/VMWare OVF Tool` to the venv’s `bin` directory.  
            * Re-activate the venv.  
    5.	Install the modules:  
        >   pip install -r requirements.txt


<br />

## **Sample csv** 

| esxi\_host   | username | password | datastore\_name        | name      | ip          | mask          | gateway    | dns            | ntp         | hostname | esxi\_internal\_nw | esxi\_external\_nw | deployment\_option |
| ------------ | -------- | -------- | ---------------------- | --------- | ----------- | ------------- | ---------- | -------------- | ----------- | -------- | ------------------ | ------------------ | ------------------ |
| 10.78.85.238 | user     | passwd   | BLR\_OTHER\_datastore1 | test\_vm3 | 10.78.85.33 | 255.255.255.0 | 10.78.85.1 | 72.163.128.140 | 10.64.58.51 | user1    | VM Network         | VM Network         | CMS1000            |
| 10.196.5.222 | user     | passwd   | datastore1 (6)         | test\_vm4 | 10.196.5.74 | 255.255.252.0 | 10.196.4.1 | 72.163.128.140 | 10.64.58.51 | user2    | VM Network         | VM Network         | VMNLite            |

<br />

## **Running the script**

> git clone https://github.com/CiscoDevNet/webex-video-mesh-node-provisioning.git 

> cd webex-video-mesh-node-provisioning 

> python3 runner.py 

<br />

## **Error messages**

### **<u> Errors before deployment </u>**

If there is invalid input in the input_data.csv, like Blank/Invalid IP, DNS, NTP etc., or issues like Duplicate VM Name or Duplicate IP, or if the ovf file is not present in the same directory, the script will not start deploying the Video Mesh Nodes. The script will return the following format of output, stating what the wrong input was, and to run the script again after validating the wrong fields.  

![invalid_csv_input](images/invalid_csv_input.png?raw=true "Title")

<br />

### **<u>Errors during/after deployment</u>**

When there are other issues that can come up while the deployment of VMN is going on, like incorrect ESXi credentials (username or password), or lack of resources on the ESXi server, then the following format of output is displayed. The nodes with incorrect credentials, or wrong datastore details, are displayed first and those nodes are not included in the progress indicator at all. The nodes which cannot be deployed due to lack of resources on the ESXi, will only show 0% in the Configuration Progress indicator. The appropriate messages will be displayed in the end, stating which nodes were deployed, and which could not be deployed (along with the reason for failure).

![final_deployment_message](images/final_deployment_message.png?raw=true "Title")




<br />

## **Troubleshooting**

When the script completes running, there are two types of log files generated. One log file is named as “vmn_provisioning.log” which contains logs of the entire process, and the other type of log file is specific to each VMN deployment, and is named as “ovf_IP.log”, where IP corresponds to the IP address of each VMN. These logs can be investigated upon further failures of the deployment.  

 _Check that all the nodes from the CSV file deployed correctly. If some nodes did not deploy, edit the CSV file to provide the necessary information and run the script again._
