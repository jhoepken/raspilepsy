from __future__ import unicode_literals

from django.db import models

# Create your models here.

class SeizureManager(models.Manager):
    def getDaysWithSeizures(self):
        import datetime, pytz

        pytz.timezone("Europe/Berlin")

        oldest = datetime.datetime.strptime(
                    datetime.datetime.strftime(
                        self.getOldestSeizure().time,
                        "%Y-%m-%d"),
                    "%Y-%m-%d")

        base = datetime.datetime.strptime(
                    datetime.datetime.strftime(
                        pytz.utc.localize(
                            datetime.datetime.today()),
                        "%Y-%m-%d"),
                     "%Y-%m-%d")
        timeRange = base-oldest
        dateRange = [base - datetime.timedelta(days=x) for x in range(0, timeRange.days)]
        return dateRange

    def getOldestSeizure(self):
        """
        Returns the oldest seizure that is stored in the database
        """
        return self.all().order_by('time')[0]
    

class Seizure(models.Model):

    time = models.DateTimeField('seizure time', auto_now_add=True)
    duration = models.IntegerField('duration in seconds')
    description = models.TextField(max_length=5000)
    objects = SeizureManager()

    def __str__(self):
        return self.description
