from django.shortcuts import render
from django.views.generic import ListView
from .models import Election, Candidate

class ElectionList(ListView):
    model = Election


class CandidateList(ListView):
    model = Candidate
