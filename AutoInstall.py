import sys
import re
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
        self.flag="false"

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
        expect_user_list.append(r"\S+@+\S+:+\/+\#+\s*")
        choice = self.expect(expect_user_list,10)
        if choice == 0:
            print("-----------")
            return
        elif choice == 1:
            self.sendline(self.username)
            self.expect(r"[Pp]assword[:]?\s*")
            self.sendline(self.password)
            return
        elif choice == 2:
            self.sendline("exit")
            return
        else:
            sys.exit("Connection Error!")

    def reinstall(self,url,tries):
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

        # self.handler.send("\n")
        time.sleep(1)
        self.handler.send("\u001b[B")
        self.handler.send("\u001b[B")
        time.sleep(1)
        for _ in range(tries):
            self.handler.send("\u001b[B")
            time.sleep(0.1)
        # self.handler.send("\u001b[B")
        self.handler.send("\n")
        self.handler.send("\n")
        # self.expect("onie-install")
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
        print("\nInstalling from {}\n".format(url))
        self.handler.send("\n")
        self.handler.send("\n")
        if self.expect(r"Installing SONiC in ONIE") == 0:
            print("Install SONIC in ONIE\n")
            self.flag = True
        return

    def verify(self,retry=1):
        time.sleep(300)
        print("Jump into verify...")
        expect_user_list = []
        expect_user_list.append(r"[Ll]ogin[:]?\s*")
        expect_user_list.append(r"[Pp]assword[:]?\s*")
        expect_user_list.append(r"\S+@+\S+:\~\$ ")
        flag = 0
        times = 0
        self.handler.expect(r"[Ll]ogin[:]?\s*",timeout=9999)
        print("login again~")
        while flag==0:
            choice = self.expect(expect_user_list)
            if choice == 0:
                self.handler.sendline(self.username)
            elif choice == 1:
                self.handler.sendline(self.password)
            elif choice == 2:
                flag=1
            elif times>5:
                print("Timeout")
                sys.exit("Timeout")
            else:
                self.handler.send("\n")
                time.sleep(10)
                times=times+1

        #
        # # self.handler.expect(r"[Ll]ogin[:]?\s*",timeout=600)
        # print("login again~")
        # self.handler.sendline(self.username)
        # self.handler.expect(r"[Pp]assword[:]?\s*", timeout=30)
        # self.handler.sendline(self.password)
        # self.handler.expect(r"\S+@+\S+:\~\$ ", timeout=30)

        i = 0
        while i < retry:
            time.sleep(60)
            self.handler.sendline("docker ps")
            self.expect(r"\S+@+\S+:\~\$ ", timeout=30)
            output = str(self.handler.before)
            for line in output.split('\n'):
                result = re.search(r"docker-syncd:", line)
            if result:
                print("Sonic reboot syccessfully!")
                sys.exit(0)
            elif not result and i<retry:
                i=i+1
                time.sleep(60)
            else:
                sys.exit("Syncd is not running.")


    def close(self):
        if not self.handler:
            sys.exit("No connection")
        self.handler.close(force=True)

if __name__=="__main__":
    c = Connection(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],"telnet","debug")
    c.connect()
    tries = 1
    if c.flag is not True and tries<=5:
        c.reinstall(sys.argv[5], tries)
        tries+=1
    elif tries>5:
        sys.exit("Fail to install.")
    c.verify(10)
    c.close()