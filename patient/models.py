from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Seizure(models.Model):

    time = models.DateTimeField('seizure time', auto_now_add=True)
    duration = models.IntegerField('duration in seconds')
    description = models.TextField(max_length=5000)

    def __str__(self):
        return self.description

