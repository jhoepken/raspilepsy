from django.contrib import admin

from .models import Seizure, PossibleSeizure

admin.site.register(Seizure)
admin.site.register(PossibleSeizure)

# Register your models here.
