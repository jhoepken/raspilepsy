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
        dateRange = [base - datetime.timedelta(days=x) for x in reversed(range(0, timeRange.days))]
        return dateRange

    def getSeizuresPerNight(self):
        from datetime import timedelta
        days = self.getDaysWithSeizures()

        seizures = []

        for day in days:
            startTime = day - timedelta(hours=10)
            endTime = day + timedelta(hours=13, minutes=59)

            seizures.append(self.filter(time__range=(startTime, endTime)))

        return seizures

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


class RawVideoCapture(models.Model):

    startTime = models.DateTimeField('start time', auto_now_add=True)
    path = models.FileField(upload_to='footage/%Y/%m/%d')


