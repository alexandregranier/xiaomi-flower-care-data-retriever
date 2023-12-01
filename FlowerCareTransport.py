import re,paramiko

FILE_NAME_REGEX = "[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}-[0-9]*-google\\.csv"
# Open a transport
host,port = "cefesftp.cefe.cnrs.fr",22
transport = paramiko.Transport((host,port))

# Auth    
username,password = "agranier","3cFm3Uf5jDMe89"


def download():
    transport.connect(None,username,password)

    # Go!    
    sftp = paramiko.SFTPClient.from_transport(transport)

    for entry in sftp.listdir_attr("."):
        mode = entry.st_mode
        if S_ISDIR(mode):
            continue
        elif S_ISREG(mode):
            if re.search(FILE_NAME_REGEX, entry.filename):
                print ("File OK")
                sftp.get(entry.filename, entry.filename)
            print(entry.filename + " is file")
        if sftp: sftp.close()
        if transport: transport.close() 
