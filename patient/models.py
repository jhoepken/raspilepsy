from __future__ import unicode_literals

from django.db import models

import datetime, pytz
from os import remove
# Create your models here.

class SeizureManager(models.Manager):
    def getDaysWithSeizures(self):

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


class PossibleSeizureFootageManager(models.Manager):

    def clean(self):
        """
        Removes false positives from the database, which are

        1. way too short in duration
        2. (maybe) don't have a manual trigger. This one needs to be decided on
            in the future.
        """
        falsePositives = self.all().order_by('-id').filter(
                hasManualTrigger=False
                ).filter(
                        footage__isnull=False
                    ).exclude(
                            footage__exact=''
                        ).filter(toBeDeleted=True)
        print falsePositives

    def update(self):
        for sI in self.all():
            sI.duration = int((sI.endTime - sI.startTime).total_seconds())
            sI.save()


class PossibleSeizureFootage(models.Model):

    startTime = models.DateTimeField('start time', auto_now_add=False)
    endTime = models.DateTimeField('end time', auto_now_add=False)
    footage = models.CharField(max_length=200)
    hasManualTrigger = models.BooleanField()
    duration = models.IntegerField(default=-1)
    toBeDeleted = models.BooleanField(default=False)

    objects = PossibleSeizureFootageManager()

    def __str__(self):
        return "%s (%i s) %r" %(self.footage, self.duration, self.hasManualTrigger)

    def save(self, *args, **kwargs):
        """
        Overloads the base-class save method, since the `hasManualTrigger` can
        be changed from other sources in the database and needs to be read. This
        change is accepted. Any other changes to data are *not accepted* and are
        hence ignored.
        """
        if self.pk is not None:
            orig = PossibleSeizureFootage.objects.get(pk=self.pk)
            self.hasManualTrigger = (orig.hasManualTrigger or self.hasManualTrigger)
        super(PossibleSeizureFootage, self).save(*args, **kwargs)

    def stop(self, args):
        pytz.timezone("Europe/Berlin")
        self.endTime = pytz.utc.localize(datetime.datetime.now())
        self.duration = int((self.endTime - self.startTime).total_seconds())
        self.save()

        if self.duration < args["min_length"]:
            # The file can be remove immideatly. The database entry cannot be
            # removed right away, though. Since we are in `self`, we cannot
            # delete `self`. In order to work around that, we mark this data set
            # as `toBeDeleted` in the database and handle the delete process in
            # the manager.
            try:
                remove(self.footage)
            except:
                pass
            self.toBeDeleted = True
            self.save()

    def start(self):

        pytz.timezone("Europe/Berlin")
        self.hasManualTrigger = False
        self.startTime = pytz.utc.localize(datetime.datetime.now())
        self.endTime = pytz.utc.localize(datetime.datetime.now())
        self.save()

