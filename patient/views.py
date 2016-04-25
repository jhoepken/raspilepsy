from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

from datetime import datetime, timedelta

from .forms import QuickAddSeizure
from patient.models import Seizure


def index(request):

    seizures = Seizure.objects.all()
    context = {'seizures': seizures}

    if request.method == 'POST':
        form = QuickAddSeizure(request.POST)
        context['form'] = form

        if form.is_valid():
            seizure = Seizure(duration=request.POST.get("duration",""), description=request.POST.get("description",""))
            seizure.save()
            form.clean()
            return HttpResponseRedirect('')
            # return render(request, 'index.html', context)

    else:
        form = QuickAddSeizure()
        context['form'] = form

    return render(request, 'index.html', context)

def monitor(request):

    seizures = Seizure.objects.all()
    context = {'seizures': seizures}

    return render(request, 'monitor.html', context)
