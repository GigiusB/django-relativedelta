# -*- coding: utf-8 -*-
from django.contrib import admin
from django.forms import ModelForm, TextInput

from .models import DemoModel

for s in (admin.site,):
    s.register(DemoModel)
