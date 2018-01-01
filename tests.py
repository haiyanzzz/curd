from django.test import TestCase

# Create your tests here.
# 批量插入数据
# booklist = []
#
# for i in range(100):
#     booklist.append(models.UserInfo(name="小花猫" + str(i), email="211" + "@qq.com" + "i*i", ut_id=i))
# models.UserInfo.objects.bulk_create(booklist)
# class Dss(object):
#     def __init__(self,name):
#         self.name= name
#         print(name)
#         print(self.name)
# aa = Dss("alex")
# print(aa.name)

# l = []
# l2 = ["ss"]
# # l.extend(l2)
# # print(l)
# l.append(l2)
# print(l)



# 函数和方法
class Foo(object):
    def __init__(self):
        self.name="haiyan"
    def func(self):
        print(self.name)

obj = Foo()
obj.func()
Foo.func(obj)

#判断函数和方法的方式
from types import FunctionType,MethodType
obj = Foo()
print(isinstance(obj.func,FunctionType))  #False
print(isinstance(obj.func,MethodType))   #True   #说明这是一个方法

print(isinstance(Foo.func,FunctionType))  #True   #说明这是一个函数。
print(isinstance(Foo.func,MethodType))  #False
