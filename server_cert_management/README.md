<h1 align = "center">Certificate Management of Video Mesh Nodes</h1>

<br />

## <a id="intro"></a> **Introduction**  

<br />

- Video Mesh customers with large number of nodes find large scale CSR creation, updation and installation of certificate time consuming.  

- This feature improves the certificate management process for the customers by reducing the amount of overall overhead.

- It creates multiple CSRs in parallel depending on the input provided by the customers.

- It also helps the customers upload and install the CA signed certificates and the private keys in bulk.

NOTE: This feature does not support separate certificate management for dual NIC.

<br />

## <a id="create-csr"></a> **Create CSR**  

Generates a certificate signing request and a private key (with optional passphrase).

### **Pre-requisites:**  
* Input Data - `input_generate.csv`: Takes all the details required for certificate generation. Each line corresponds to a different request.
    
Note: Edit the csv file to include all details. Refer to the [sample csv](#sample-csv-generate) attached below for more details.

### <a id="sample-csv-generate"></a> **Sample csv:** 

<br />

| video\_mesh\_node | username | password | common\_name        | email              | san               | org     | org\_unit | locality | state     | country | passphrase       | key\_bit\_size |
|-------------------| -------- | -------- |---------------------|--------------------|-------------------|---------|-----------|----------|-----------|---------|------------------|----------------|
| 1.1.1.1           | user1     | passwd1   | test1.example.com   | email1.example.com | test1.example.com |Cisco   | IT        | BLR      | KA        | IN      | passphrase       | 2048           |
| 2.2.2.2           | user2     | passwd2   | 2.2.2.2   |  |  |   |         |       |         |       |        |            |
| test3.example.com   | test3_user | passwd3   | test3.example.com   | email3.example.com | test3.example.com\|test4.example.com   | Cisco   | IT        | BLR      | KA        | IN      |        | 4096|



* video_mesh_node - The IP/FQDN of the Video Mesh Node to add the External IP details. (mandatory)
* username - The username of the node. (mandatory)
* password - The password of the node. (mandatory)
* common_name - IP/FQDN of the Video Mesh Node given as common name. (mandatory)
* email - User's Email Address. (optional)
* san - Subject Alternative Name(s) (optional). Multiple pipe-delimited ( | ) FQDNs are allowed. If provided, it must contain the common name. If san is not provided, it takes the common_name as the value of san.
* org - Organization/ Company name. (optional)
* org_unit - Organizational Unit or Department or Group Name, etc. (optional)
* locality - City/Locality. (optional)
* state - State/Province. (optional)
* country - Country/Region. Two-letter abbreviation. Do not provide more than two letters. (optional)
* passphrase - Private Key Passphrase. (optional)
* key_bit_size - Private Key Bit Size. Accepted values are: 2048(by default) and 4096. (optional)

### **Execution** 

> git clone https://github.com/CiscoDevNet/webex-video-mesh-node-provisioning.git 

> pip install -r requirements.txt

> cd webex-video-mesh-node-provisioning/server_cert_management/

> Edit the input_generate.csv to include details

> python3 create_csr.py --action [action_to_perform]

        usage: create_csr.py [-h] --action {generate,downloadCert,downloadKey,deleteCert,deleteKey}

        CSR creation
        
        optional arguments:
          -h, --help            show this help message and exit
          --action {generate,downloadCert,downloadKey,deleteCert,deleteKey}
                                Action to perform


#### **Generate certificates and private keys**
This will generate the CSR and store the certificates and the private keys by creating folders as node names/IPs provided in the input file and then downloading them under the respective folders.

> python3 create_csr.py --action generate

- The certificate that gets downloaded is `videoMeshCsr.csr`

- The private key that gets downloaded is `VideoMeshGeneratedPrivate.key`

#### **Download certificates**
To download the certificate again, run the following.

> python3 create_csr.py --action downloadCert

- The certificate that gets downloaded is `videoMeshCsr.csr`

#### **Download private keys**
To download the private key again, run the following.

> python3 create_csr.py --action downloadKey

- The private key that gets downloaded is `VideoMeshGeneratedPrivate.key`

#### **Delete certificates**
To delete the certificate, run the following. 

> python3 create_csr.py --action deleteCert

#### **Delete private keys**
To delete the private key, run the following. 

> python3 create_csr.py --action deleteKey


#### **Note**

_The password in the csv is masked by `******` for every row whose action was successful, and by `######` for every row whose action was failed. Enter the password again for the failed rows if the script is re-run. Do not share the original csv file with anyone as it contains password as plaintext._

<br />

## <a id="install-cert"></a> **Upload and Install**

- Once the customer has the CA certificate available with them, they can go ahead to upload and install it along with the private key to respective nodes.

- This feature allows the customer to upload the server certificates (.crt or .pem files) and the private keys to the Video mesh nodes and install them in bulk.

- If the certificate is already installed, the same process can be used to re-install a new certificate. Firstly, the new certificate and the key can be uploaded and then installed.

### **Pre-requisites:**  
* Input Data - `input_install.csv`: Takes all the details required for uploading and installing the certificates in bulk. The customer can provide multiple Video Mesh Nodes for certificate installation as input in each row.
    
Note: Edit the csv file to include all details. Refer to the [sample csv](#sample-csv-install) attached below for more details.

### <a id="sample-csv-install"></a> **Sample csv:** 

<br />

| video\_mesh\_node | username    | password | cert\_source      | ca\_cert         | passphrase | private\_key                  |
|-------------------| ------------| -------- |-------------------|------------------|-------------------------------|----------|
| 1.1.1.1           | user1       | passwd1  | 1.1.1.1           | videoMeshCsr.crt | passphrase | VideoMeshGeneratedPrivate.key |
| 2.2.2.2           | user2       | passwd2  | 2.2.2.2           | videoMeshCsr.crt |   | VideoMeshGeneratedPrivate.key |
| test3.example.com | test3_user | passwd3  | test3.example.com | videoMeshCsr.crt |   | VideoMeshGeneratedPrivate.key |
| test4.example.com | test4_user | passwd4  | test3.example.com | videoMeshCsr.crt |   | VideoMeshGeneratedPrivate.key |


* video_mesh_node - The IP/FQDN of the Video Mesh Node where the certificate and the private key need to be installed. (mandatory)
* username - The username of the node. (mandatory)
* password - The password of the node. (mandatory)
* cert_source - Source directory of the CA certificate and the private key on the system from where it will be uploaded to the video mesh node. The customer needs to put the CA signed certificate and private key in the source directory before running the script. (mandatory)
* ca_cert - CA signed certificate (mandatory)
* passphrase - Private Key passphrase. This field is required for `uploadKey` option if the passphrase was provided while CSR creation, else the upload will fail. (optional)
* private_key - Private key (mandatory)

### **Execution** 

> git clone https://github.com/CiscoDevNet/webex-video-mesh-node-provisioning.git

> pip install -r requirements.txt

> cd webex-video-mesh-node-provisioning/server_cert_management/

> Edit the input_install.csv to include details

> python3 install_cert.py --action [action_to_perform]

        usage: install_cert.py [-h] --action {uploadCert,uploadKey,install,downloadCertCA,deleteCertCA}

        CA Certificate Installation

        optional arguments:
            -h, --help            show this help message and exit
            --action {uploadCert,uploadKey,install,downloadCertCA,deleteCertCA}
                        Action to perform


#### **Upload CA certificates**
- To upload the CA signed certificates for the Video Mesh Nodes provided in the input file. The CA certificates (.pem or .csr files) should be placed in the folders (same as cert_source column value in the input file). 
- If the folder does not exist or the file is not present in the respective folder, it will give an error.

- Place the CA certificate under node directory (eg: webex-video-mesh-node-provisioning/server_cert_management/test3.example.com/videoMeshCsr.crt) and execute the following.

> python3 install_cert.py --action uploadCert

#### **Upload private keys**
- To upload the private keys for the Video Mesh Nodes provided in the input file. The private keys should be placed in the folders (same as cert_source column value in the input file).
- If the folder does not exist or the file is not present in the respective folder, it will give an error.

- Place the private key (if not already present) under node directory (eg: webex-video-mesh-node-provisioning/server_cert_management/test3.example.com/VideoMeshGeneratedPrivate.key) and execute the following.
    
> python3 install_cert.py --action uploadKey


#### **Install certificates and private keys**
To install the uploaded CA signed certificates and private keys to the Video Mesh Nodes.

> python3 install_cert.py --action install

- To renew/reload/reinstall, the same process can be repeated. Re-upload the files using `uploadCert` and `uploadKey` options and then use the `install` option to install them.

#### **Download CA certificates**
To download the installed CA signed certificates for the Video Mesh Nodes. This script downloads all the CA certificates for the nodes in respective directories of their FQDN/IP values (directory is created if it already does not exist).

> python3 install_cert.py --action downloadCertCA

#### **Delete CA certificates**
To delete the installed CA signed certificates for the Video Mesh Nodes.

> python3 install_cert.py --action deleteCertCA

#### **Note**

_The password in the csv is masked by `******` for every row whose action was successful, and by `######` for every row whose action was failed. Enter the password again for the failed rows if the script is re-run. Do not share the original csv file with anyone as it contains password as plaintext._

---