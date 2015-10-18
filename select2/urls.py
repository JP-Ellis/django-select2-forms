try:
    from django.conf.urls import patterns, url
except ImportError:
    from django.conf.urls.defaults import patterns, url


urlpatterns = patterns(
    '',
    url(r'^(?P<app_label>[^\/]+)/(?P<model_name>[^\/]+)/(?P<field_name>[^\/]+)/$',
        'select2.views.fetch_items', name='select2_fetch_items'),
)
