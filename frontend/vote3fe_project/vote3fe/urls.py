from django.conf.urls import url
from vote3fe import views

urlpatterns = [
    url(r'^elections/$', views.ElectionList.as_view()),
    url(r'^candidates/$', views.CandidateList.as_view()),
    url(r'^generate_vote_codes/$', views.generate_vote_codes,
        name='generate_vote_codes'),
    url(r'^vote_codes/([0-9]+)/([0-9]+)/$', views.VoteCodesList.as_view(),
        name='vote_codes'),
    url(r'^vote_code/(?P<votecode_param>.{22})/$', views.vote_code,
        name='vote_code'),
    url(r'^vote/(?P<votecode_param>.{22})/(?P<election>[0-9]+)/$', views.vote,
        name='vote'),
    url(r'^audit/$', views.AuditEntryList.as_view()),
    url(r'^audit/(?P<pk>[0-9]+)/$', views.AuditEntryDetail.as_view(),
        name='audit_entry'),
    url(r'^audit/(?P<pk>[0-9]+)/raw/$', views.AuditEntryRawDetail.as_view(),
        name='audit_entry_raw'),
    url(r'^audit/count/$', views.audit_entry_count, {'raw': False},
        name='audit_count'),
    url(r'^audit/count/raw/$', views.audit_entry_count, {'raw': True},
        name='audit_count_raw'),
]
