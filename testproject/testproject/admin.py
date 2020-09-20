from django.contrib import admin

from demoproject.testapp.models import Interval


@admin.register(Interval)
class IntervalAdmin(admin.ModelAdmin):
    list_display = ['value']
    list_filter = ['value']
