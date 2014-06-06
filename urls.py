from django.conf.urls.defaults import *
from monitor.views import view_index, websites, website_html, alarms, website_details, delete_obj, webthumb, probe_one_website, probe_all_websites, verify_up, verify_down, fix_website, ports_view, port_return, wget_view, wget_details, fix_sites, probe_down_websites, mobile_api, count_stats, generate_csv, generate_weekly_uptime

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', view_index),
    (r'^delete/(?P<deltype>[-\w]+)/$', delete_obj),
    (r'^ports/$', ports_view),
    (r'^websites/$', websites),
    (r'^website_html/$', website_html),
    (r'^details/website/(?P<slug>[-\w]+)/$', website_details),
    (r'^details/wget/(?P<slug>[-\w]+)/$', wget_details),
    (r'^alarms/$', alarms),
    (r'^fixsites/$', fix_sites),
    (r'^wget/$', wget_view),
    (r'^runstats/$', count_stats),
    (r'^webthumb/$', webthumb),
    (r'^details/csv/(?P<slug>[-\w]+)/$', generate_csv),
    (r'^runuptime/$', generate_weekly_uptime),
    (r'^api/websites/return/$', port_return),
    (r'^api/mobile/$', mobile_api),
    (r'^probe_one_website/$', probe_one_website),
    (r'^probe_all_websites/$', probe_all_websites),
    (r'^probe_down_websites/$', probe_down_websites),
    (r'^verify_up/$', verify_up),
    (r'^verify_down/$', verify_down),
)
