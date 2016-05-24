from django.contrib import admin

from .models import Seizure, \
        PossibleSeizureFootage, \
        Patient, \
        PatientMotion, \
        Sleep

admin.site.register(Seizure)
admin.site.register(PossibleSeizureFootage)
admin.site.register(Patient)
admin.site.register(PatientMotion)
admin.site.register(Sleep)

# Register your models here.
