# -*- coding:utf-8 -*-
# @Time    : 2018/6/25 1:23
# @Author  : Brady
# @File    : __init__.py
# @Software: PyCharm
# @Contact : bradychen1024@gmail.com

from functools import wraps


def convert_parameter(new_params=None):
    """
    :param new_params: 要转换成新值的常量字典，为空则不转换
    :return:将被装饰函数中的参数(必须为字典)的值进行转换，返回新参数的函数运行结果
    example:
    @convert_parameter({'name':'brady'})
    def func(*args, **kwargs):
        print('arg结果：', args)
        print('kwarg结果：', kwargs)
    if __name__ == '__main__':
        func({'name':'becky'}, new_name={'name':'alice'})
    """
    def _convert_parameter(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def update(param_dict):
                if isinstance(param_dict, dict):
                    for key in param_dict.keys():
                        param_dict.update({key: new_params.get(key)}) if new_params.get(key) else ''
            if new_params:
                [update(arg) for arg in args]
                [update(arg) for _, arg in kwargs.items()]
            return func(*args, **kwargs)
        return wrapper
    return _convert_parameter
