

import socket
import sys
import time
from paramiko.py3compat import u

# windows does not have termios...
try:
    import termios
    import tty

    has_termios = True
except ImportError:
    has_termios = False


def interactive_shell(chan):
    if has_termios:
        posix_shell(chan)
    else:
        windows_shell(chan)



def posix_shell(chan):
    import select
    # 获取原tty属性
    oldtty = termios.tcgetattr(sys.stdin)# 恢复终端原始状态，每按一个键就发送
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)#设置会话超时时间
        cmd = []
        # f = open('ssh_test.log','w')
        while True:
            # 通过select.select 监听chan（打开的通道（和远程服务器连接的状态））, sys.stdin（输入），一旦变化就写入r
            # 监视 用户输入 和 远程服务器返回数据（socket）
            # 阻塞，直到句柄可读
            r, w, e = select.select([chan, sys.stdin], [], [])
            # 当chan变化时，加入到r，远程服务器发送内容过来
            if chan in r:
                try:
                    x = u(chan.recv(1024))# Python3用这个
                    if len(x) == 0:
                        sys.stdout.write('\r\n*** EOF\r\n')
                        break
                    sys.stdout.write(x)# 写入缓冲区
                    sys.stdout.flush()# 刷新，将缓冲区内容显示出来
                except socket.timeout:
                    pass
            # 当sys.stdin 放入r中时，将获取到的内容发送到远程服务器
            if sys.stdin in r:
                x = sys.stdin.read(1)# 读取一个字符
                if len(x) == 0:
                    break
                if x == '\r':#输入回车，把回去到字符拼接为完整命令
                    print('input>', ''.join(cmd))
                    # log = "%s   %s\n" %(time.strftime("%Y-%m-%d %X", time.gmtime()), ''.join(cmd))
                    # print(log)
                    chan.models.AuditLog.objects.create(
                        user=chan.crazyeye_account,
                        log_type=1,
                        host_to_remote_user=chan.host_to_user_obj,
                        content=''.join(cmd)
                    )
                    # f.write(log)
                    cmd = []
                else:
                    cmd.append(x)
                chan.send(x)# 发送一个字符

    finally:
        # 重新设置终端属性,将终端状态还原
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        # f.close()


# thanks to Mike Looijmans for this code
def windows_shell(chan):
    print("window chan", chan.host_to_user_obj)
    print("window chan", chan.crazyeye_account)
    import threading

    sys.stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")

    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write('\r\n*** EOF ***\r\n\r\n')
                sys.stdout.flush()
                break
            sys.stdout.write(str(data))
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass
