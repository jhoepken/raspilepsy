from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^monitor/$', views.monitor, name='monitor'),
    url(r'^monitor/statistics$', views.monitorStatistics, name='monitorStatistics'),
    url(r'^monitor/statistics/seizureDistribution.png$', views.seizureDistribution, name='seizureDistribution'),
    url(r'^monitor/statistics/seizureFrequency.png$', views.seizureFrequency, name='seizureFrequency'),
    url(r'^monitor/statistics/dailySeizureDistributionComparison.png$',
        views.dailySeizureDistributionComparison,
        name='dailySeizureDistributionComparison'),

    url(r'^camera$', views.index, name='index'),
]

