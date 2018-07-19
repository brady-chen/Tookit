# -*- coding: utf-8 -*-
import socket
import queue
import traceback

from multiprocessing import freeze_support
from multiprocessing.managers import BaseManager
from threading import Thread

# 发送任务的队列:
task_queue = queue.Queue()
# 接收结果的队列:
result_queue = queue.Queue()

"""
简单的分布式demo
"""


def return_task_queue():
    global task_queue
    return task_queue


def return_result_queue():
    global result_queue
    return result_queue


class TaskDistribution:
    def __init__(self, host, port, authkey, func):
        """
        :param host: 服务器ip
        :param port: 端口
        :param authkey: 授权键
        :param func: 运行的函数
        """
        self.host = host
        self.func = func
        try:
            self.manager = BaseManager(address=(host, port), authkey=authkey)
        except TypeError:
            self.manager = BaseManager(address=(host, port), authkey=authkey.encode('utf-8'))
        BaseManager.register('get_task_queue', callable=return_task_queue)
        BaseManager.register('get_result_queue', callable=return_result_queue)

    def start_master(self):
        """
        主机
        """
        self.manager.start()
        task = self.manager.get_task_queue()
        result = self.manager.get_result_queue()
        try:
            while True:
                """task.put(something)"""
                while not task.qsize() < 1000:
                    # 限制任务队列长度，减少占用内容
                    _ = result.get()
        except Exception as error:
            print(error)
            print(traceback.format_exc())
        finally:
            self.manager.shutdown()
            print('master exit.')

    def start_slave(self):
        """
        从机
        """
        self.manager.connect()
        func = self.func
        task = self.manager.get_task_queue()
        result = self.manager.get_result_queue()
        # 多线程运行
        while True:
            try:
                for i in range(2):
                    args = task.get()
                    t = Thread(target=func, args=(args,))
                    t.setDaemon(True)
                    t.start()
                    result.put(args)
                t.join()
            except IOError as e:
                print(e)
                break
            except queue.Empty:
                print('task queue is empty.')
        # 处理结束:
        print('worker exit.')

    def start(self):
        freeze_support()
        local_name = socket.getfqdn(socket.gethostname())
        ip = socket.gethostbyname(local_name)
        # print myname, ip, self.host
        if ip == self.host:
            self.start_master()
        else:
            self.start_slave()
            

if __name__ == '__main__':
    t = TaskDistribution('localhost', 8180, 'brady', lambda a: print(a))
    t.start()
