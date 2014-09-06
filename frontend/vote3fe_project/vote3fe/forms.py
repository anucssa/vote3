from django import forms
from .models import Election

class GenerateVoteCodesForm(forms.Form):
    elections = forms.ModelMultipleChoiceField(
        queryset=Election.objects.all(),
        to_field_name='name')
    count = forms.IntegerField(initial=1, min_value=1)

    
