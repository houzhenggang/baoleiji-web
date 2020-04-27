from django.contrib import admin

# Register your models here.

from myweb import models

admin.site.register(models.Host)
admin.site.register(models.HostGroup)
admin.site.register(models.HostToRemoteUser)
admin.site.register(models.RemoteUser)
admin.site.register(models.UserProfile)
admin.site.register(models.IDC)


