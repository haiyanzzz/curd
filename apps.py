from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules

class StarkConfig(AppConfig):
    name = 'stark'  #应用名称

    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """
        autodiscover_modules('stark')  #在应用中创建的py文件和这个名字一样
