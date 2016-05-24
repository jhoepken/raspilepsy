from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.utils import translation
import logging

from os.path import join

from .forms import QuickAddSeizure
from patient.models import Seizure, PossibleSeizureFootage

import patient.video

def index(request):

    # Uncomment these lines, to force GERMAN language. Just to check the
    # translation.
    # request.LANGUAGE_CODE = 'de'
    # translation.activate('de')

    seizures = Seizure.objects.all()
    context = {'seizures': seizures}

    if request.method == 'POST':
        form = QuickAddSeizure(request.POST)
        context['form'] = form

        if form.is_valid():
            seizure = Seizure(
                        duration=request.POST.get("duration",""),
                        description=request.POST.get("description","")
                        )
            seizure.save()
            form.clean()
            return HttpResponseRedirect('')

    else:
        form = QuickAddSeizure()
        context['form'] = form

    return render(request, 'index.html', context)

def seizureNow(request):
    """
    Handles the request that is triggert by the user, if the button "Seizure
    Now" on the Dashbord is pressed. Which in turn finds the current
    `PossibleSeizureFootage` and marks it as User selected. If there is none,
    the last one is used.
    """

    if request.POST["action"] == "seizureNow":
        
        newSeizure = Seizure()
        newSeizure.duration = 1
        newSeizure.description = ''
        newSeizure.save()

        try:
            s = PossibleSeizureFootage.objects.all().order_by('-id')[0]
            s.hasManualTrigger = True
            s.seizure = newSeizure
            s.save()
        except IndexError:
            newSeizure.delete()

    seizures = Seizure.objects.all()
    context = {'seizures': seizures}

    form = QuickAddSeizure()
    context['form'] = form

    return render(request, 'index.html', context)

def sleepRegister(request):
    """
    This function handles the user interactions in the panel for registering
    sleep rythms.
    """

    if request.POST["action"] == "sleep":
        pass

    elif request.POST["action"] == "wakeUp":
        pass

    seizures = Seizure.objects.all()
    context = {'seizures': seizures}

    form = QuickAddSeizure()
    context['form'] = form

    return render(request, 'index.html', context)

def camera(request):
    if request.POST["action"] == "cameraStart":
        print "STARTING CAMERA"
        patient.video.running = True

    elif request.POST["action"] == "cameraStop": 
        print "STOPPING CAMERA"

    return render(request, 'index.html', {})



def monitor(request):

    seizures = Seizure.objects.all().order_by('-time')
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

    time = sorted([seizure.time for seizure in seizures])
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
    from numpy import mean, array, max

    seizures = Seizure.objects.all()

    days = Seizure.objects.getDaysWithSeizures()

    seizureFrequency = [len(sI) for sI in Seizure.objects.getSeizuresPerNight()]

    time = [seizure.time for seizure in seizures]
    durationMean = []
    for seizure in Seizure.objects.getSeizuresPerNight():
        durationMean.append(mean([sI.duration for sI in seizure]))


    durationMeanNorm = durationMean/max(durationMean)

    error_config = {'ecolor': '0.3'}
    fig=Figure(facecolor="white",figsize=(12, 6))
    ax=fig.add_subplot(111)
    # ax.set_xlabel("Time")
    ax.set_ylabel("Seizures [-]")
    ax.grid(True)
    p = ax.bar(
            days,
            seizureFrequency,
            yerr=durationMeanNorm,
            error_kw=error_config
            )

    i = 0
    for pI in p:
        height = pI.get_height()
        ax.text(pI.get_x() + pI.get_width()/2., height+durationMeanNorm[i],
                    '%1.2fs' %durationMean[i],
                    ha='center',            # vertical alignment
                    va='bottom'             # horizontal alignment
                    )
        i += 1
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()

    canvas=FigureCanvas(fig)

    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response

def dailySeizureDistributionComparison(request):
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    from datetime import timedelta
    from numpy import array as npArray

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

    plots = []
    labels = []
    for setI in range(len(duration)):
        p, = ax.plot(
                    npArray(time[setI]) - timedelta(days=setI, hours=-2),
                    duration[setI],
                    marker='o'
                    )
        plots.append(p)
        labels.append("%s" %time[setI][0].strftime("%d-%m-%Y"))


    fig.legend(plots, labels, 'upper right', bbox_to_anchor=(1.01, 1))
    fig.autofmt_xdate()
    ax.grid(True)
    ax.set_xlabel("Time of sampling interval [h]")
    ax.set_ylabel("Seizure duration [s]")

    canvas=FigureCanvas(fig)
    response=HttpResponse(content_type='image/png')
    canvas.print_png(response)

    return response
