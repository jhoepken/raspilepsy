from django import forms

class QuickAddSeizure(forms.Form):

    duration = forms.CharField(label='Seizure Duration in seconds', max_length=4)
    description = forms.CharField(label='Description', widget=forms.Textarea)

class WeeklyReportForm(forms.Form):

    week = forms.ChoiceField(choices=[(x, x) for x in range(1, 32)])

