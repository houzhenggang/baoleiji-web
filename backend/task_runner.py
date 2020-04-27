import sys ,os,json
import time,socket
from concurrent.futures import ThreadPoolExecutor

import paramiko


def ssh_cmd(sub_task_obj):
    print("start therad ",sub_task_obj)
    host_to_user_obj = sub_task_obj.host_to_remote_user

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host_to_user_obj.host.ip_addr,
                    port=host_to_user_obj.host.port,
                    username=host_to_user_obj.remote_user.username,
                    password=host_to_user_obj.remote_user.password,
                    timeout=5)
        stdin, stdout, stderr = ssh.exec_command(sub_task_obj.task.content,timeout=10)
        stdout_res = stdout.read()
        stderr_res = stderr.read()

        #task_log_obj = models.TaskLogDetail.objects.get(task=task_obj,host_to_remote_user_id=host_to_user_obj.id)
        sub_task_obj.result =stdout_res + stderr_res
        print("------------result-------------")
        print(sub_task_obj.result)

        if stderr_res:
            sub_task_obj.status = 2
        else:
            sub_task_obj.status = 1
    except Exception as e:
        sub_task_obj.result = e
        sub_task_obj.status = 2

    sub_task_obj.save()
    ssh.close()


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(base_dir)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "baoleiji.settings")
    import django
    django.setup()
    from django import conf
    from myweb import models

    if len(sys.argv) == 1:
        exit("task id not provided!")
    task_id = sys.argv[1]#主进程id
    task_obj = models.Task.objects.get(id=task_id)#根据主进程id获取数据中与之关联对象，可以拿到主机、执行的命令等
    print("task runner..",task_obj)
    #最多10个线程一起执行
    pool = ThreadPoolExecutor(10)

    if task_obj.task_type == 'cmd':
        for sub_task_obj in task_obj.tasklogdetail_set.all():
            pool.submit(ssh_cmd, sub_task_obj)  # 通过submit函数提交执行的函数到线程池中，submit函数立即返回，不阻塞
            # pool.submit(ssh_cmd,task_obj.tasklogdetail_set.first())
            # ssh_cmd(task_obj.tasklogdetail_set.all()[2])

    #当线程池调用该方法时, 线程池的状态则立刻变成SHUTDOWN状态。此时，则不能再往线程池中添加任何任务，否则将会抛出RejectedExecutionException异常。
    # 但是，此时线程池不会立刻退出，直到添加到线程池中的任务都已经处理完成，才会退出

    pool.shutdown(wait=True)