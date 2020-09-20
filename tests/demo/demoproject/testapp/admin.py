# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import DemoModel

for s in (admin.site,):
    s.register(DemoModel)
