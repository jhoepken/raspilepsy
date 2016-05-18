from django.contrib import admin

from .models import Seizure, PossibleSeizureFootage, Patient, PatientMotion

admin.site.register(Seizure)
admin.site.register(PossibleSeizureFootage)
admin.site.register(Patient)
admin.site.register(PatientMotion)

# Register your models here.
