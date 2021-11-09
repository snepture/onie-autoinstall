import sys
import time
import pexpect

'''

python AutoInstall.py hostname port username password url

'''


class Connection(object):

    def __init__(self,hostname,port,username,password,protocol,debug):
        self.hostname=hostname
        self.port=port
        self.username=username
        self.password=password
        self.protocol=protocol
        self.debug=debug

    def expect(self,param,timeout=None):
        a = self.handler.expect(param,timeout=timeout)
        if self.debug:
            print(self.handler.before.decode('utf-8'))
            print(a)
            print(self.handler.after.decode('utf-8'))
            print("---------------------------")
        return a

    def sendline(self,param):
        return self.handler.sendline(param)

    def connect(self):
        if self.protocol == "ssh":
            self._ssh()
        else:
            self._telnet()

    def _ssh(self):
        ssh_command = 'ssh  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -l {} {} -p {}'.format(self.username, self.hostname, self.port)
        self.handler = pexpect.spawn(ssh_command)
        self.expect(r"(?i)password[:]?\s*$")
        # s.expect("Password:")
        self.sendline(self.password)
        try:
            self.expect(r"[>#$]\s?",timeout=5)
        except pexpect.TIMEOUT:
            raise Exception("Device {} Login failed".format(self.hostname))

    def _telnet(self):
        self.handler = pexpect.spawn('telnet {} {}'.format(self.hostname, self.port))
        self.sendline("\n")
        expect_user_list = []
        expect_user_list.append(r"\S+@+\S+:\~\$ ")
        expect_user_list.append(r"[Ll]ogin[:]?\s*")
        # expect_user_list.append(r"[>#\$]\s?")
        choice = self.expect(expect_user_list,10)
        if choice == 0:
            print("-----------")
            return
        if choice == 1:
            self.sendline(self.username)
            self.expect(r"[Pp]assword[:]?\s*")
            self.sendline(self.password)
            return
        # if choice == 2:
        #     self.sendline("end")
        # try:
        #     self.expect(r":~$\s*")
        #     print("success")
        #     pass
        # except pexpect.TIMEOUT:
        #     raise Exception("Device {} Login failed".format(self.hostname))

    def reinstall(self,url=None):
        def reboot():
            command = "sudo reboot"
            self.handler.send("{}\n".format(command))

        if not self.handler:
            self.connect()

        reboot()
        time.sleep(3)
        self.handler.send("\u001b[B")
        self.handler.send("\u001b[B")
        self.handler.send("\u001b[B")
        self.expect(r"before booting or `c' for a command-line")

        self.handler.send("\n")
        time.sleep(1)
        self.handler.send("\u001b[B")
        self.handler.send("\u001b[B")
        time.sleep(1)
        self.handler.send("\u001b[B")
        self.handler.send("\u001b[B")
        # time.sleep(1)
        # self.handler.send("\u001b[B")
        # self.handler.send("\u001b[B")
        self.handler.send("\n")
        self.handler.send("\n")
        time.sleep(30)
        self.handler.send("\n")
        self.handler.send("\n")
        self.handler.sendline("onie-discovery-stop\n")

        time.sleep(30)
        self.handler.send("\n")
        self.handler.send("\n")
        self.handler.sendline("onie-discovery-stop\n")
        self.handler.send("\n")
        self.handler.send("\n")
        self.handler.send("\n")
        time.sleep(5)
        self.handler.sendline("onie-nos-install {}".format(url))
        self.handler.send("\n")
        self.handler.send("\n")
        return

    def close(self):
        if not self.handler:
            print("No connection\n")
        self.handler.close(force=True)

if __name__=="__main__":
    sys.argv[1]
    c = Connection(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],"telnet","debug")
    c.connect()
    c.reinstall(sys.argv[5])
    #"http://11.1.1.69/yecsong-sonic-400G-20210930.bin"
