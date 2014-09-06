from django.conf.urls import url
from .views import ElectionList, CandidateList

urlpatterns = [
    url(r'^elections/$', ElectionList.as_view()),
    url(r'^candidates/$', CandidateList.as_view()),
]
