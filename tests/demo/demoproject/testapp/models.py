# -*- coding: utf-8 -*-
import logging

from django.db import models

from relativedeltafield import RelativeDeltaField

logger = logging.getLogger(__name__)


# class DemoAllModel(models.Model):
#     choice = StrategyClassField(registry=registry)
#     multiple = MultipleStrategyClassField(registry=registry)
#     custom = StrategyField(registry=registry1)
#     custom_multiple = MultipleStrategyField(registry=registry1)


class DemoModel(models.Model):
    interval = RelativeDeltaField(blank=True, null=True)
    mandatory_interval = RelativeDeltaField()

    def __str__(self):
        return str(self.interval) + " .. " + str(self.mandatory_interval)


class Interval(models.Model):
    value = RelativeDeltaField(null=True, blank=True)
