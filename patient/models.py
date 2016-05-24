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
        return "%is: %s" %(self.duration, self.description)


class PossibleSeizureFootageManager(models.Manager):

    def clean(self):
        """
        Removes false positives from the database, which have been marked as to
        be deleted previously. This method solely does the cleaning up and *not*
        the selection. If the footage file is still present, it is removed as
        well.
        """
        for fPI in self.getFalsePositives():
            try:
                remove(fPI.footage)
            except:
                pass
            fPI.delete()


    def getFalsePositives(self):
        """
        Returns a list of `PossibleSeizureFootage` instances that have already
        been marked as `toBeDeleted` and can be savely be deleted.
        """
        return self.all().order_by('-id').filter(toBeDeleted=True)

    def update(self):
        for sI in self.all():
            sI.duration = int((sI.endTime - sI.startTime).total_seconds())
            sI.save()


class PossibleSeizureFootage(models.Model):
    """
    Points to a single video footage file and serves the purpose of
    encapsulating e.g. video footage of multiple sources for a single seizure
    and correlating it to a seizure. It has hence a one-to-many relation to
    `Seizure`.
    """

    startTime = models.DateTimeField('start time', auto_now_add=False)
    endTime = models.DateTimeField('end time', auto_now_add=False)
    footage = models.CharField(max_length=200)
    hasManualTrigger = models.BooleanField()
    duration = models.IntegerField(default=-1)
    toBeDeleted = models.BooleanField(default=False)

    seizure = models.ForeignKey(
                    Seizure,
                    default=-1,
                    on_delete=models.CASCADE
                )

    objects = PossibleSeizureFootageManager()

    def __str__(self):
        return "%s (%i s) %r %r" %(
                self.footage,
                self.duration,
                self.hasManualTrigger,
                self.toBeDeleted
                )

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
            try:
                if orig.seizure.id > self.seizure.id:
                    self.seizure = orig.seizure
            except:
                pass
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

class Patient(models.Model):
    """
    Stores data of a patient. This is *unencrypted* for now, but the data is not
    sensitive. It is solely personal information.
    """
    firstname = models.CharField(max_length=50)
    surname = models.CharField(max_length=50)
    weight = models.FloatField()
    height = models.FloatField()
    language = models.CharField(max_length=2, default='de')

    def __str__(self):
        return "%s, %s" %(self.surname, self.firstname)

class PatientMotion(models.Model):
    """
    Stores the motion of a patient in the database, so that it can be updated
    from various sources. Doing this simplifies various computations of time
    calculations as well and encapulates time and motion data.
    """

    lastMotionTime = models.DateTimeField('lastMotionTime', auto_now_add=False)
    isInMotionSince = models.DateTimeField('isInMotionSince', auto_now_add=False)
    isInMotion = models.BooleanField(default=False)

    patient = models.ForeignKey(
                    Patient,
                    default=-1,
                    on_delete=models.CASCADE
                )

    def __str__(self):
        return "%s, %s" %(self.patient.surname, self.patient.firstname)

    def moves(self):
        """
        This method needs to be called if motion of a patient is detected by any
        means.
        """
        pytz.timezone("Europe/Berlin")
        self.lastMotionTime = pytz.utc.localize(datetime.datetime.now())

        if not self.isInMotion:
            self.isInMotionSince = pytz.utc.localize(datetime.datetime.now())
            self.isInMotion = True

        self.save()

    def freezes(self):
        """
        This method needs to be called if the patient stops moving.
        """
        self.isInMotion = False
        self.save()

class SleepManager(models.Manager):

    def isSleeping(self):
        try:
            return self.all().order_by('-startTime')[0]
        except IndexError:
            return False


class Sleep(models.Model):

    startTime = models.DateTimeField('startTime', auto_now_add=False)
    endTime = models.DateTimeField('endTime', auto_now_add=False)
    isSleeping = models.BooleanField(default=False)

    patient = models.ForeignKey(
                    Patient,
                    default=-1,
                    on_delete=models.CASCADE
                )

    objects = SleepManager()

    def start(self):
        pytz.timezone("Europe/Berlin")
        self.startTime = pytz.utc.localize(datetime.datetime.now())
        self.endTime = pytz.utc.localize(datetime.datetime.now())
        self.isSleeping = True
        self.save()

    def stop(self):
        pytz.timezone("Europe/Berlin")
        self.endTime = pytz.utc.localize(datetime.datetime.now())
        self.isSleeping = False
        self.save()
