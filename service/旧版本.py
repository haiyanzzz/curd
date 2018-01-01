#!usr/bin/env python
# -*- coding:utf-8 -*-
from django.shortcuts import render,HttpResponse
from django.conf.urls import url
class StarkConfig(object):
    list_display = []
    def __init__(self, model_class, site):
        self.model_class = model_class
        self.site = site
    def change_list_views(self,request,*args,**kwargs):
        data_list = self.model_class.objects.all()
        '''展示th的信息'''
        head_list = []
        for field_name in self.list_display:
            if isinstance(field_name,str):
                verbose_name = self.model_class._meta.get_field(field_name).verbose_name
            else:
                verbose_name = field_name(self,is_header=True)
            head_list.append(verbose_name)

         '''展示td的信息'''
        # [["id","name"],["id","name"],["id","name"],]
        new_data_list = []
        for row in data_list:
            temp = []
            for field_name in self.list_display:
                if isinstance(field_name,str):
                    #如果是字符串类型的就是用getattr的方式，因为对象不能.字符串
                    val = getattr(row,field_name)
                else:
                    val = field_name(self,row)
                temp.append(val)
            new_data_list.append(temp)



            '''如果list_display为空的时候显示对象'''
            if not self.list_display:
                new_data_list=[]
                for item in data_list:
                    temp = []
                    temp.append(item)
                    new_data_list.append(temp)
            return render(request, "stark/change_list_views.html", {"head_list":head_list,"data_list":new_data_list})

        return render(request, "stark/change_list_views.html", {"head_list":head_list,"data_list":data_list})


    def add_views(self,request,*args,**kwargs):
        return HttpResponse("添加页面")

    def delete_view(self, request,nid, *args, **kwargs):
        return HttpResponse("删除页面")

    def change_views(self, request,nid, *args, **kwargs):
        return HttpResponse("修改页面")

    def get_urls(self):
        app_model_name = (self.model_class._meta.app_label,self.model_class._meta.model_name)
        all_url = [
            url(r'^$', self.change_list_views,name="%s_%s_changelist"%app_model_name),
            url(r'^add/$', self.add_views,name="%s_%s_add"%app_model_name),
            url(r'^(\d+)/delete/$', self.delete_view,name="%s_%s_delete"%app_model_name),
            url(r'^(\d+)/change/$', self.change_views,name="%s_%s_change"%app_model_name),
        ]
        all_url.extend(self.extra_urls())
        return all_url
    def extra_urls(self):
        return []

    @property
    def urls(self):
        return self.get_urls()

class StarkSite(object):
    def __init__(self):
        self._registry ={}
        '''
        _registry = {
					models.Role: StarkConfig(models.Role,v1.site),
					models.UserInfo: StarkConfig(models.UserInfo,v1.site)
					models.UserType: StarkConfig(models.UserType,v1.site)
					models.Article: StarkConfig(models.Article,v1.site)
				}
		'''
    def register(self,model_class,stark_config_class=None):
        if not stark_config_class:
            '''stark_config_class是类对象，如果没有这个类就重新赋值，去执行StarkConfig'''
            stark_config_class = StarkConfig
        self._registry[model_class] = stark_config_class(model_class,self)

    def get_urls(self):
        url_list = []
        for model_calss,stark_config_obj in self._registry.items():
            app_name = model_calss._meta.app_label#应用名称
            model_name = model_calss._meta.model_name#表的名称
            cur_url = url(r'^{0}/{1}/'.format(app_name,model_name),(stark_config_obj.urls,None,None))
            #这是的stark_config_obj是上面StarkConfig的实例对象。stark_config_obj.urls就会去找上面类的urls
            url_list.append(cur_url)
        return url_list
    @property #吧方法当属性来用
    def urls(self):
        return (self.get_urls(),None,'stark')
site = StarkSite()
