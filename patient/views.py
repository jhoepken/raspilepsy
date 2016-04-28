from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader

from os.path import join

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

    else:
        form = QuickAddSeizure()
        context['form'] = form

    return render(request, 'index.html', context)

def monitor(request):

    seizures = Seizure.objects.all()
    context = {'seizures': seizures}

    return render(request, 'monitor.html', context)

def monitorStatistics(request):

    seizures = Seizure.objects.all()
    context = {'seizures': seizures}


    return render(request, 'monitorStatistics.html', context)

def seizureDistribution(request):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter

    seizures = Seizure.objects.all()
    context = {'seizures': seizures}

    time = [seizure.time for seizure in seizures]
    duration = [seizure.duration for seizure in seizures]

    fig=Figure(facecolor="white",figsize=(12, 6))
    ax=fig.add_subplot(111)
    # ax.set_xlabel("Time")
    ax.set_ylabel("Seizure Duration [s]")
    ax.grid(True)
    ax.plot_date(time, duration, '-', marker='o')
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d %H:%M'))
    fig.autofmt_xdate()

    canvas=FigureCanvas(fig)

    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response

def seizureFrequency(request):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter

    seizures = Seizure.objects.all()

    days = Seizure.objects.getDaysWithSeizures()
    seizureFrequency = [len(sI) for sI in Seizure.objects.getSeizuresPerNight()]

    time = [seizure.time for seizure in seizures]
    # duration = [seizure.duration for seizure in seizures]

    fig=Figure(facecolor="white",figsize=(12, 6))
    ax=fig.add_subplot(111)
    # ax.set_xlabel("Time")
    ax.set_ylabel("Seizures [-]")
    ax.grid(True)
    ax.bar(days, seizureFrequency)
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    # fig.autofmt_xdate()

    canvas=FigureCanvas(fig)

    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response

def dailySeizureDistributionComparison(request):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    from datetime import timedelta
    import numpy as np

    import seaborn as sns
    sns.set(style="darkgrid", palette="Set2")
    
    seizureFrequency = Seizure.objects.getSeizuresPerNight()
    fig=Figure(facecolor="white",figsize=(12, 6))
    ax=fig.add_subplot(111)

    duration = []
    time = []
    for day in seizureFrequency:
        duration.append([dayI.duration for dayI in day])
        time.append([dayI.time for dayI in day])

    for setI in range(len(duration)):
        ax.plot(np.array(time[setI]) - timedelta(days=setI), duration[setI])
    fig.autofmt_xdate()
    ax.grid(True)

    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response
