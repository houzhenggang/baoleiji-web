import json
from myweb import models
import subprocess
from django import conf

class MultiTaskManger(object):
    def __init__(self,request):
        self.request = request
        self.run_task()

    def task_parser(self):
        """解析任务"""
        self.task_data = json.loads(self.request.POST.get('task_data'))
        task_type = self.task_data.get('task_type')

        #通过反射拿到函数cmd对象并执行
        if hasattr(self,task_type):
            task_func = getattr(self,task_type)
            task_func()
        else:
            print("cannot find task ",task_type)

    def run_task(self):
        """调用任务"""

        self.task_parser()

    def cmd(self):
        """批量命令
        1. 生成任务在数据库中的记录,拿到任务id
        2.触发任务, 不阻塞
        3.返回任务id给前端
        """

        #在task表中创建记录，可以获取到主任务id
        task_obj = models.Task.objects.create(
            task_type = 'cmd',
            content = self.task_data.get('cmd'),
            user = self.request.user
        )

        #初始化子任务表中的数据
        selected_host_ids = set(self.task_data['selected_hosts'])
        task_log_objs =[]
        for id in selected_host_ids:
            task_log_objs.append(
                models.TaskLogDetail(task=task_obj,host_to_remote_user_id=id,result='init...')
            )
        #每创建一个对象都保存一次数据，会增加开销，如果先批量创建对象，最后保存一次到数据库.可以使用bulk_create方法
        models.TaskLogDetail.objects.bulk_create(task_log_objs)

        task_script = "python %s/backend/task_runner.py %s" % (conf.settings.BASE_DIR, task_obj.id)
        #Popen对象创建后，主程序不会自动等待子进程完成。我们必须调用对象的wait()方法，父进程才会等待 (也就是阻塞block)
        #调用多线程执行task_runner.py，实现登录服务器执行相关脚本
        cmd_process = subprocess.Popen(task_script, shell=True)
        print("running batch commands....")
        self.task_obj = task_obj