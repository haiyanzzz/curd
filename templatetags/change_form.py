#!usr/bin/env python
# -*- coding:utf-8 -*-
from django.template import Library
from django.urls import reverse
from stark.service.v1 import site

register = Library()
@register.inclusion_tag("stark/form.html")
def form(config,model_form_obj):
    from django.forms import ModelChoiceField
    from django.forms.boundfield import BoundField  # 数据都封装在这个类了
    new_form = []
    for bfield in model_form_obj:
        dic = {"is_popup": False, "item": bfield}  # 每一个bfield就是Form的字段，是一个对象
        if isinstance(bfield.field, ModelChoiceField):
            # print(bfield.field,"popup按钮")
            print(bfield, type(bfield))  # <class 'django.forms.boundfield.BoundField'>
            releated_model_name = bfield.field.queryset.model  # 找到关联的类名
            if releated_model_name in site._registry:
                app_model_name = releated_model_name._meta.app_label, releated_model_name._meta.model_name  # 找到应用名和类名（目的是拼接url）
                #FK,onetoone,M2M,当前字段所在的类名和releated_name
                model_name = config.model_class._meta.model_name
                related_name = config.model_class._meta.get_field(bfield.name).rel.related_name
                print(model_name,related_name,"model_name,related_name")

                base_url = reverse("stark:%s_%s_add" % (app_model_name))
                popup_url = "%s?_popupbackid=%s&model_name=%s&related_name=%s" % (base_url, bfield.auto_id,model_name,related_name)  #每一个input框的id
                print(bfield.auto_id,"111111")
                dic["is_popup"] = True
                dic["popup_url"] = popup_url
        new_form.append(dic)
    return {"form":new_form}   #返回的这个form是给了"stark/form.html"它里面的form,然后循环遍历