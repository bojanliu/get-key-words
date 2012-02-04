from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^text/', include('text.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
    (r'^$','get-key-words.views.gkw'),
    (r'^over/$',direct_to_template,{'template':'over.html'}),
    url(r'^download/$','gkw.views.download',name='download'),
    (r'^static/(?P<path>.*)$','django.views.static.serve',{'document_root':settings.STATIC_PATH,}),
)
