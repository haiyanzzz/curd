#!usr/bin/env python
# -*- coding:utf-8 -*-
import copy
from django.db.models import Q
from django.shortcuts import render,HttpResponse,redirect
from django.conf.urls import url
from django.urls.base import reverse
from django.utils.safestring import mark_safe
from django.forms import ModelForm
from pager.pager import Pagination
from django.http import QueryDict
import json
from django.db.models.fields.reverse_related import ManyToOneRel
class FilterOption(object):
    """
    处理配置的组合条件
    """
    def __init__(self, field_name, is_multi=False, is_choice=False, condition=None,text_func_name=None,val_func_name=None):
        """
        :param field_name: 条件对应的字段名称（字符串）
        :param is_multi: 是否多选
        :param is_choice:  是否为choices字段，否则就是外键或者多对多
        :param condition: 字段的筛选条件
        :param text_func_name: 组合搜索时，页面上生成显示文本的函数
        :param val_func_name: 组合搜索时，页面上生成的a标签的值的函数
        """
        self.field_name = field_name
        self.is_multi = is_multi
        self.is_choice = is_choice
        self.condition = condition
        self.text_func_name = text_func_name
        self.val_func_name = val_func_name

    def get_querySet(self,_field):
        """
        获得外键关联表的数据
        :return:
        """
        if self.condition:
            querySet = _field.rel.to.objects.filter(**self.condition)
        else:
            querySet = _field.rel.to.objects.all()
        return querySet

    def get_choices(self, _field):
        """
        获得字段内的choice
        :return:
        """
        return _field.choices


class FilterRow(object):
    """
    组合条件中的一行 就是此类的一个对象
    """

    def __init__(self, option, data,  request):
        self.data = data
        self.option = option
        self.request = request

    def __iter__(self):
        params = copy.deepcopy(self.request.GET)
        path_info = self.request.path_info
        params._mutable = True
        current_id = params.get(self.option.field_name)
        current_id_list = params.getlist(self.option.field_name)

        # =================全部按钮===================
        if self.option.field_name in params:
            # 如果当前字段在request.GET中，代表该条件已被选中，全部按钮应为非active状态
            # href 目的：为了去掉params中的gender # del params[self.option.field_name]
            origin_list = params.pop(self.option.field_name)  # 删掉request.GET中的gender
            url = "{0}?{1}".format(path_info,params.urlencode())
            yield mark_safe("<a href='{0}'>{1}</a>".format(url, '全部'))
            params.setlist(self.option.field_name, origin_list)  # ??????????
        else:
            # 如果当前字段不在request.GET中，代表该条件未被选中，全部按钮应为active状态
            # 保留原有params
            url = "{0}?{1}".format(path_info, params.urlencode())
            yield mark_safe("<a href='{0}' class='active'>{1}</a>".format(url, '全部'))

        # ================普通按钮====================
        for val in self.data:   #单选
            if self.option.is_choice: # ((1,'男'),(2,'女'),(1,'男'))
                pk, text = str(val[0]),val[1]
            else:  # 外键或多对多
                '''现在的做法，是由于关联的字段变了depart = models.ForeignKey(verbose_name='部门', to="Department",to_field="code")'''
                text = str(self.option.text_func_name(val)) if self.option.text_func_name else str(val)
                pk = str(self.option.val_func_name(val)) if self.option.val_func_name else str(val.pk)
                #原来的做法 pk, text = str(val.pk), str(val)

            if not self.option.is_multi:
                # 单选行的普通按钮
                params[self.option.field_name] = pk  # request.GET['gender'] = 1
                print(params,"zhy")
                url = "{0}?{1}".format(path_info,params.urlencode()) # http://127.0.0.1:8000/index/app03/userinfo/?gender=1
                print(current_id,pk)
                if current_id == pk:
                    print(111111111)
                    val = mark_safe("<a href='{0}' class='active'>{1}</a>".format(url, text))
                else:
                    val = mark_safe("<a href='{0}'>{1}</a>".format(url, text))
          # ================多选的普通按钮===============
            else:
                # 多选行的普通按钮
                _params = copy.deepcopy(params)
                id_list = _params.getlist(self.option.field_name) #从url中得到  [1,2]
                if pk in current_id_list:
                    # 如果按钮的pk出现在url中，说明此按钮是激活状态
                    # 构造一个href，目的是将url中的此pk去掉
                    id_list.remove(pk)  # 将此pk去掉
                    _params.setlist(self.option.field_name, id_list)  # 将新的id_list设置到request.GET中
                    url = "{0}?{1}".format(path_info, _params.urlencode())
                    val = mark_safe("<a href='{0}' class='active'>{1}</a>".format(url, text))
                else:
                    # 如果按钮的pk不在url中，说明此按钮是非激活状态
                    # 构造一个href，目的是将url中加上这个pk
                    id_list.append(pk)  # 加上此pk
                    _params.setlist(self.option.field_name, id_list)  # 将新的id_list设置到request.GET中
                    url = "{0}?{1}".format(path_info, _params.urlencode())
                    val = mark_safe("<a href='{0}'>{1}</a>".format(url, text))

            yield val  # 传什么值循环的时候打印什么值

class ChangeList(object):
    '''将列表页面的功能封装到此类中'''
    def __init__(self,config,queryset):
        self.config = config
        self.list_display= config.get_list_display
        self.model_class = config.model_class
        self.request = config.request
        self.show_add_btn = config.get_show_add_btn()
        self.show_search_form = config.get_show_search_form()
        self.show_search_val = config.request.GET.get(config.search_key,"")
        self.actions = config.get_actions()
        self.show_actions = config.get_show_actions()
        self.comb_filter = config.get_comb_filter()
        self.edit_link = config.get_edit_link()
        self.show_comb_filter = config.get_show_comb_filter()
        # 分页
        data_list_count = queryset.count()
        pager_obj = Pagination(self.request.GET.get('page', 1), data_list_count, self.request.path_info, self.request.GET,per_page_count=5)
        page_html = pager_obj.page_html()
        self.pager_obj = pager_obj
        self.data_list = queryset[pager_obj.start:pager_obj.end]
        self.page_html = page_html

        # self.add_url = config.get_add_url()
    def add_url(self):
        return self.config.get_add_url()

    def head_list(self):
        '''构造表头'''
        '''展示th的信息'''
        head_list = []
        for field_name in self.list_display():
            if isinstance(field_name, str):
                '''如果是字符串，就直接让显示他的verbose_name'''
                verbose_name = self.model_class._meta.get_field(field_name).verbose_name
            else:
                '''否则的话自己去设置th的内容'''
                verbose_name = field_name(self, is_header=True)
            head_list.append(verbose_name)

        return head_list

    def body_list(self):
        '''展示td的信息'''
        # [["id","name"],["id","name"],["id","name"],]
        new_data_list = []
        for row in self.data_list:
            temp = []
            for field_name in self.list_display():
                if isinstance(field_name, str):  # 判断field_name对象是不是字符串
                    # 如果是字符串类型的就是用getattr的方式，因为对象不能.字符串
                    val = getattr(row, field_name)  # row."id"
                    #用于定制编辑列
                    if field_name in self.edit_link:
                        val = self.edit_link_tag(row.pk,val)
                else:
                    val = field_name(self.config, row)
                temp.append(val)
            new_data_list.append(temp)

        '''如果list_display为空的时候显示对象'''
        if not self.list_display:
            new_data_list = []
            for item in self.data_list:
                temp = []
                temp.append(item)
                new_data_list.append(temp)
            return new_data_list
        return new_data_list

    def modify_actions(self):
        result = []
        for func in self.actions:
            temp = {"name": func.__name__, "text": func.short_desc}
            result.append(temp)
        return result

    def gen_comb_filter(self):
        # ["gender","depart","roles"]
        data_list = []
        from django.db.models import ForeignKey,ManyToManyField
        for option in self.comb_filter: # [op1,op2,op3]
            _field = self.model_class._meta.get_field(option.field_name)#得到字段
            if isinstance(_field,ForeignKey):  #判断这个字段是不是ForeignKey这个类的实例
                row = FilterRow(option, option.get_querySet(_field), self.request)
            elif isinstance(_field,ManyToManyField):
                row = FilterRow(option, option.get_querySet(_field), self.request)
            else:
                row = FilterRow(option, option.get_choices(_field), self.request)
            yield row

        '''data_list=[
                ((1,"男"),(2，“女”)),
                [<Department: 销售部>, <Department: 外交部>],
                [obj,obj,obj],
        ]
        '''

    def edit_link_tag(self,pk,text):
        params = QueryDict(mutable=True)
        query_str = self.request.GET.urlencode()  #page=1
        params[self.config._query_param_key] = query_str
        #要跳转的路径http://127.0.0.1:8080/index/crm/department/1/change/?_listfilter=None%3D
        return mark_safe("<a href='%s?%s'>%s</a>"%(self.config.get_change_url(pk),params.urlencode(),text))

class StarkConfig(object):
    '''
    处理增删改查的基类
    '''
    def __init__(self, model_class, site):
        self.model_class = model_class
        self.site = site
        self.request = None
        self._query_param_key = "_listfilter"  #如果在构造方法里面修改了，就统一都变了， 所以就比自己写死的好
        self.search_key = "p"

    list_display = []
    # =================url相关，reverse反向解析=============
    def get_change_url(self,nid):
        name = "stark:%s_%s_change"%(self.model_class._meta.app_label,self.model_class._meta.model_name)
        edit_url = reverse(name,args=(nid,))  #反向解析只要找到他的name属性，就会找到他对应的路径
        return edit_url

    def get_add_url(self):
        name = "stark:%s_%s_add" % (self.model_class._meta.app_label, self.model_class._meta.model_name)
        edit_url = reverse(name)
        return edit_url

    def get_delete_url(self, nid):
        name = "stark:%s_%s_delete" % (self.model_class._meta.app_label, self.model_class._meta.model_name)
        edit_url = reverse(name,args=(nid,))
        return edit_url

    def get_list_url(self):
        name = "stark:%s_%s_changelist" % (self.model_class._meta.app_label, self.model_class._meta.model_name)
        edit_url = reverse(name)
        return edit_url

    # ===============吧删除，编辑，复选框设置默认按钮==================

    def checkbox(self,obj=None,is_header=False):
        if is_header:
            return "选择"
        return mark_safe("<input type='checkbox' name='pk' value='%s'/>"%obj.id)

    def edit(self,obj=None,is_header=False):
        if is_header:
            return "操作"
        #获取条件
        query_str = self.request.GET.urlencode()
        if query_str:
            #重新构造
            params = QueryDict(mutable=True)
            params[self._query_param_key] = query_str
            return mark_safe("<a href='%s?%s'>编辑</a>" % (self.get_change_url(obj.id),params.urlencode(),))
        return mark_safe("<a href='%s'>编辑</a>"%(self.get_change_url(obj.id),))


    def delete(self,obj=None,is_header=False):
        if is_header:
            return "删除"
        #动态跳转路径，反向解析，因为每次都要用到，我们可以吧它封装到一个函数
        return mark_safe("<a href='%s'>删除</a>"%self.get_delete_url(obj.id))

    #做默认的删除和编辑。对这个方法重写的时候可以吧权限管理加进去，
    # 当它都什么权限的时候显示什么按钮。
    def get_list_display(self):
        data = []
        if self.list_display:
            data.extend(self.list_display) #在新的列表里面吧list_display扩展进来
            # data.append(StarkConfig.edit)  #因为是默认的，直接在类里面去调用edit
            data.append(StarkConfig.delete)
            data.insert(0,StarkConfig.checkbox)
        return data

    show_add_btn = True
    # ======这个方法可自定制（如果把show_add_btn设置为False就不会显示添加按钮）=====
    def get_show_add_btn(self):
        return self.show_add_btn

    # 1、==============关键字搜索==============
    search_fields = []
    def get_search_fields(self):
        result = []
        if self.search_fields:
            result.extend(self.search_fields)
        # print(result) # ['name', 'email']
        return result
    # =============是否显示搜索框==============
    show_search_form = False
    def get_show_search_form(self):
        return self.show_search_form


    # ===================整合Q查询的================
    def get_search_condition(self):
        key_word = self.request.GET.get(self.search_key)
        # print(key_word)
        search_fileds = self.get_search_fields()  # 拿到搜索字段
        condition = Q()
        condition.connector = "or"
        if key_word and self.get_show_search_form():
            for fields_name in search_fileds:
                condition.children.append((fields_name, key_word))
            print(condition)
        return condition


    # 2、================actions==============
    actions = []  #默认是没值的
    def get_actions(self):
        result = []
        if self.actions:
            result.extend(self.actions)
        return result

    # =============是否显示搜索框==============
    show_actions = False
    def get_show_actions(self):
        return self.show_actions

    # =============组合搜索====================
    comb_filter = []
    def get_comb_filter(self):
        result = []
        if self.comb_filter:
            result.extend(self.comb_filter)
        return result

    show_comb_filter = False
    def get_show_comb_filter(self):
        return self.show_comb_filter
    # =============编辑链接================
    edit_link = []
    def get_edit_link(self):
        result = []
        if self.edit_link:
            result.extend(self.edit_link)
        return result

    # ============自定义order_by排序==============
    order_by = []
    def get_order_by(self):
        result = []
        if self.order_by:
            result.extend(self.order_by)
        return result
    # =================请求处理的视图================
    def change_list_views(self,request,*args,**kwargs):
        # 处理actions
        if request.method =="POST":
            func_name_str = request.POST.get("list_action")  #mutil_del
            print("zccc",func_name_str)
            action_func = getattr(self,func_name_str)
            ret = action_func(request)  #执行函数
            if ret:
                return ret

        # ========处理组合条件查询============
        print(self.request.GET)
        print(self.get_comb_filter())

        comb_filter_dict = {}  # 条件字典
        for filter_obj in self.get_comb_filter():
            # queryset.filter(**{gender__in:1,gender__in:2})
            # 目的是构造这样的语句：queryset.filter('gender__in'=[1],'depart__in'=[2],)
            #循环配置
            if filter_obj.field_name in self.request.GET.keys():
                #如果配置中的字段名字在request.GET.keys中，将字段名赋值给字典的key
                value_list = request.GET.getlist(filter_obj.field_name)
                comb_filter_dict[filter_obj.field_name+'__in'] = value_list

        queryset = self.model_class.objects.filter(self.get_search_condition()).filter(**comb_filter_dict).order_by(*self.get_order_by()).distinct()
        cl = ChangeList(self,queryset)
        return render(request, "stark/change_list_views.html", {"cl":cl})

    model_form_class=None
    def get_model_form_class(self):
        if self.model_form_class:   #如果自己定制了就用自己的，在这就什么也不返回了，如果没有自己定义就返回默认的这个Form
            return self.model_form_class
        # 方式一定义ModelForm
        # class TestModelForm(ModelForm):
        #     class Meta:
        #         model = self.model_class
        #         fields = "__all__"
        # return TestModelForm
        # 方式二定义
        Meta = type("Meta", (object,), {"model": self.model_class, "fields": "__all__"})
        TestModelForm = type("TestModelForm", (ModelForm,), {"Meta": Meta})
        return TestModelForm

    def add_views(self,request,*args,**kwargs):
        model_form_class = self.get_model_form_class()
        _popupbackid = request.GET.get("_popupbackid")
        if request.method=="GET":
            form = model_form_class()
            return render(request,"stark/add_view.html",{"form":form,"config":self})
        else:
            form = model_form_class(request.POST)
            if form.is_valid():
                # 数据库中创建数据
                new_obj = form.save()
                if _popupbackid: #如果是popup请求
                    # render一个页面，写自执行函数

                    result = {"status":False,"id":None,"text":None,"popupbackid":_popupbackid}
                    model_name = request.GET.get("model_name")
                    related_name = request.GET.get("related_name")
                    print(new_obj._meta.related_objects,"xxxx111")
                    for related_obj in new_obj._meta.related_objects:  #new_obj所有关联的对象
                        _model_name = related_obj.field.model._meta.model_name  #关联字段所在的表名
                        _related_name = related_obj.related_name  #找到关联的related_name
                        _limit_choices_to = related_obj.limit_choices_to   #找到关联的limit_choices_to
                        print("111111144444",_model_name,_related_name,_limit_choices_to)
                        if (type(related_obj) == ManyToOneRel):
                            '''如果是Fk才找下面的，如果是多对多是没有_field_name的'''
                            _field_name = related_obj.field_name
                        else:
                            _field_name = 'pk'
                        if model_name==_model_name and related_name==str(_related_name):
                            is_exits = self.model_class.objects.filter(**_limit_choices_to,pk=new_obj.pk).exists()
                            if is_exits:
                                #如果新创建的用户时，只有是销售部的人，页面才增加
                                #分门别类做判断
                                result["status"] = True
                                result["text"] = str(new_obj)
                                result["id"] = getattr(new_obj,_field_name)
                                return render(request, "stark/popupback.html",{"json_result": json.dumps(result, ensure_ascii=False)})
                    return render(request,"stark/popupback.html",{"json_result":json.dumps(result,ensure_ascii=False)})
                else:
                    return redirect(self.get_list_url())
            return render(request, "stark/add_view.html", {"form": form,"config":self})

    def delete_view(self, request,nid, *args, **kwargs):
        self.model_class.objects.filter(pk=nid).delete()
        return redirect(self.get_list_url())

    def change_views(self, request,nid, *args, **kwargs):
        model_form_class = self.get_model_form_class()
        obj = self.model_class.objects.filter(pk=nid).first()
        if not obj:
            return redirect(self.get_list_url())
        if request.method == "GET":
            form = model_form_class(instance=obj)
            return render(request, "stark/edit_view.html", {"form": form,"config":self})
        else:
            form = model_form_class(data=request.POST,instance=obj)
            if form.is_valid():
                form.save()
                list_query_str = request.GET.get(self._query_param_key)
                list_url = "%s?%s"%(self.get_list_url(),list_query_str)
                return redirect(list_url)
            else:
                return render(request, "stark/edit_view.html", {"form": form,"config":self})

    # =============路由系统，对应相应的视图函数=====================
    def wrap(self,view_func):
        def inner(request,*args,**kwargs):
            self.request = request
            '''因为默认的编辑，删除，添加等那里面的函数没有request参数，而我们又用到这个参数，
            ，所以在每次执行函数的时候给传一个request,由于每个都要用，所以加一个装饰器
            '''
            return view_func(request,*args,**kwargs)
        return inner

    def get_urls(self):
        app_model_name = (self.model_class._meta.app_label,self.model_class._meta.model_name)
        all_url = [
            url(r'^$', self.wrap(self.change_list_views),name="%s_%s_changelist"%app_model_name),
            url(r'^add/$', self.wrap(self.add_views),name="%s_%s_add"%app_model_name),
            url(r'^(\d+)/delete/$', self.wrap(self.delete_view),name="%s_%s_delete"%app_model_name),
            url(r'^(\d+)/change/$', self.wrap(self.change_views),name="%s_%s_change"%app_model_name),
        ]
        all_url.extend(self.extra_urls())
        return all_url

    # ===========额外扩展url(用户可以进行随意扩展)==========
    def extra_urls(self):
        return []

    @property
    def urls(self):
        return self.get_urls()
class StarkSite(object):
    '''单例模式，用于保存model类和处理这个类增删改查的配置类的对象'''
    def __init__(self):
        self._registry ={}  #放置处理请求对应关系
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
        #如果用户自己传进去类了，就用自己的，自己的需要继承StarkConfig。如果自己没有就找基类的，自己有就用自己的

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
        return (self.get_urls(),None,'stark')  #第三个参数是namesapce
site = StarkSite()   #实例化
