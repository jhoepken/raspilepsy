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
