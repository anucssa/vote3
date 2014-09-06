from django.conf.urls import patterns, include, url
from django.contrib import admin
import vote3fe

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'vote3fe_project.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),

    url(r'^vote/', include('vote3fe.urls', namespace='vote3fe')),
)
