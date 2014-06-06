from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.template.defaultfilters import slugify
from google.appengine.api import users, mail, urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.api import oauth
from datetime import datetime, timedelta
from monitor.models import *
from random import choice

def display_twitter():                 
    import feedparser
    d = feedparser.parse("http://search.twitter.com/search.atom?q=%23kelvin")

    entry_list = d['entries'][0:3]
    twitter_obj_list = []
    for i in entry_list:
        twitter_obj_list.append(i.content[0].value)
        
    return twitter_obj_list
    
def view_index(request):

    user = users.get_current_user()
    website_list = Website.all()
    website_total = website_list.count(999999)
    
    alert_list = AlertHistory.all()
    alert_total = alert_list.count(999999)
    twitter_obj_list = display_twitter()
    
    return render_to_response("index.html", {   
                                'alert_total': alert_total,
                                'twitter_obj_list': twitter_obj_list,
                                'website_total': website_total,
                                'login_url': users.create_login_url("/websites/"),
                                },)
                                
                                
def randstring(length=10):
    valid_chars='ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrszy23456789'
    return ''.join((choice(valid_chars) for i in xrange(length)))


# http://localhost:8080/api/websites/return/?ip=10.180.18.132&probe_loc=au&ttlb=10                                
def port_return(request):
    ip_addr = request.GET.get('ip')
    ttlb = request.GET.get('ttlb')
    probe_loc = request.GET.get('probe_loc')        

    q = Port.all()
    q.filter("ip_addr =", ip_addr)
    result = q.get()
    
    if result.status == 'Up' and int(ttlb) == 0:
        p = check_down(result)
    elif result.status == 'Down' and int(ttlb) > 0:
        p = check_up(result)
        
    if probe_loc == 'au' or probe_loc == 'uk' or probe_loc == 'us' :
        Probe(port=result,
                ttlb=int(ttlb),
                probe_loc=probe_loc).put()
    else:
        return HttpResponseRedirect("/")

    result.put()
    
    return HttpResponse("OK")
                  

                                
def ports_view(request):
    user = users.get_current_user()
    if user:
        watcher = Watcher.get_or_insert(user.user_id())
        #website_list = db.get(watcher.websites)
    return render_to_response("index.html", {   
                                'login_url': users.create_login_url("/websites/"),
                                },)
  
  
def wget_details(request, slug):
    user = users.get_current_user()
    if user:
        wget = Watcher.get_or_insert(user.user_id())
        if request.method == 'GET':
            q = Wget.all()
            q.filter("slug =", slug)
            wget_obj = q.get()
        else:
            wget_obj = None
            
        return render_to_response("wget_details.html", {   
                        'user': user,
                        'wget': wget_obj,
                        'logout_url': users.create_logout_url("/"),
                        },)
    else:
        return HttpResponseRedirect(users.create_login_url("/wget/"))
        
        
  
def wget_view(request):
    user = users.get_current_user()

    if user:
        watcher = Watcher.get_or_insert(user.user_id())
        
        if request.method == 'POST':
            form = WgetForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data['name']
                start_time = form.cleaned_data['start_time']
                end_time = form.cleaned_data['end_time']
                dow = form.cleaned_data['dow']
                wget_key = name + str(user.user_id())
                wget = Wget.get_or_insert(str(wget_key))
                if wget.name == None:
                    wget.name = name
                    wget.slug = randstring(25)
                    wget.api_code = randstring(12)
                    wget.start_time = start_time
                    wget.end_time = end_time
                    wget.dow = dow
                    wget.put()
                    
                    
                if watcher.user == None:
                    watcher.user = user
                    watcher.put()
                if wget.key() not in watcher.wgets:
                    watcher.wgets.append(wget.key())
                    watcher.put()
                    
            
        else:
            form = WgetForm()
        
        wget_list = db.get(watcher.wgets)
        return render_to_response("wget.html", {  
                        'wget_list': wget_list, 
                        'user': user,
                        'form': form,
                        'logout_url': users.create_logout_url("/"),
                        },)
                        
    else:
        return render_to_response("index.html", {   
                                    'login_url': users.create_login_url("/websites/"),
                                    },)
                            
def timediff(btime, stime):
    from datetime import timedelta, time
    """Difference between two datetime.time objects
    Accepts two datetime.time objects where btime > stime
    Returns a datetime.time object of the difference in time of
    the two datetime objects.
    """
    btdelta = timedelta(hours=btime.hour, minutes=btime.minute, seconds=btime.second)
    stdelta = timedelta(hours=stime.hour, minutes=stime.minute, seconds=stime.second)
    tdiff = btdelta - stdelta
    tdiffsec = tdiff.seconds
    if tdiffsec < 60 and tdiffsec > 0:
        return time(0, 0, int(tdiffsec))
    elif tdiffsec < 3600 and tdiffsec > 0:
        tdiffsplit = str(tdiffsec/60.0).split('.')
        tdiffmin = int(tdiffsplit[0])
        tdiffsec = float("0."+tdiffsplit[1])*60
        return time(0, int(tdiffmin), int(tdiffsec))
    elif tdiffsec > 0:
        tdiffhourmin = str(tdiffsec/3600.0).split('.')
        tdiffhour = int(tdiffhourmin[0])
        tdiffminsec = str(float("0."+tdiffhourmin[1])*60).split('.')
        tdiffmin = int(tdiffminsec[0])
        tdiffsec = float("0."+tdiffminsec[1])*60
        return time(tdiffhour, tdiffmin, int(tdiffsec))
    else:
        return time(0, 0, 0)
                
def calc_uptime(website_obj, q_days):
    q_days = datetime.now()-timedelta(days=q_days)
    alert_q = AlertHistory.all()
    alert_q = alert_q.filter('website =', website_obj)
    alert_list = alert_q.filter('end_date >', q_days) 
    total_down = 0
    
    for p in alert_list:
        if p.end_date == None: # still open
            t_diff = timediff(now, p.start_date)
        else: #closed, convert
            t_diff =timediff(p.end_date, p.start_date)
        total_down = total_down + (t_diff.hour * 60) + t_diff.minute
    return total_down

def generate_weekly_uptime(request):
    from datetime import datetime, time, timedelta, date
    
    total_avail = 60
    now = datetime.now()
    datetime.now()
    today = datetime.today()

    website_list = Website.all()
    for website_obj in website_list:
        total_down = calc_uptime(website_obj, 7)
        
        d_history = DowntimeHistory(website=website_obj, num=total_down)
        d_history.save()
        
    return HttpResponse("OK")
                         
         
def websites(request):
    user = users.get_current_user()

    if user:
        watcher = Watcher.get_or_insert(user.user_id())
        website_list = db.get(watcher.websites)

        if request.method == 'POST':
            form = WebsiteForm(request.POST)

            if form.is_valid():

                url_key = form.cleaned_data['url']
                #website = form.save(commit=False)

                #url_key = form.cleaned_data.get('url')
                #print url_key

                
                website = Website.get_or_insert(str(url_key))

                if website.url == None:
                    website.url = url_key
                    website.slug = randstring(25)
                    website.status = 'Up'
                    website.put()

                if watcher.user == None:
                    watcher.user = user
                    watcher.put()
                if website.key() not in watcher.websites:
                    watcher.websites.append(website.key())
                    watcher.put()
        else:
            form = WebsiteForm()

        if len(website_list) > 14 or (request.method == 'POST' and len(website_list) == 14):
            form = None
            
        return render_to_response("websites.html", {   
                        'website_list': website_list,
                        'user': user,
                        'form': form,
                        'logout_url': users.create_logout_url("/"),
                        },)
                        
    else:
        return render_to_response("index.html", {   
                                    'login_url': users.create_login_url("/websites/"),
                                    },)
                                    
def fix_sites(request):
    website_list = Website.all()
    for x in website_list:
        if x.slug == None:
            x.slug = randstring(25)

def website_details(request, slug):
    user = users.get_current_user()
    if user:
        watcher = Watcher.get_or_insert(user.user_id())
        if request.method == 'GET':
            thirty_days = datetime.now()-timedelta(days=30)
            q = Website.all()
            q.filter("slug =", slug)
            website_obj = q.get()

            alert_q = AlertHistory.all()
            alert_q = alert_q.filter('website =', website_obj)
            alert_q = alert_q.filter('end_date >', thirty_days) 
           
            alert_list = alert_q.order("-end_date")

            total_down = calc_uptime(website_obj, 30)
            avail = str(100 - (float(total_down)/43200.0)*100)[0:5]
            
        return render_to_response("website_details.html", {   
                        'user': user,
                        'website': website_obj,
                        'alert_list': alert_list,
                        'avail': avail,
                        'logout_url': users.create_logout_url("/"),
                        },)
    else:
        return HttpResponseRedirect(users.create_login_url("/websites/"))

def delete_obj(request, deltype):
    user = users.get_current_user()
    if user:
        watcher = Watcher.get_or_insert(user.user_id())
        if request.method == 'POST':
            url = request.POST.get('url')
            q = Website.all()
            q.filter("url =", url)
            website_obj = q.get()

            alert_q = AlertHistory.all()
            alert_q = alert_q.filter('watcher =', watcher)
            alert_list = alert_q.filter('website =', website_obj)
            if alert_list.count() > 0:
                for alert in alert_list:
                    alert.delete()
            
            if website_obj.key() in watcher.websites:
                watcher.websites.remove(website_obj.key())
                watcher.put()
                if website_obj.members.count() == 0:
                    website_obj.delete()
            

        return HttpResponseRedirect("/websites/")
    else:
        return HttpResponseRedirect(users.create_login_url("/websites/"))
                      
def website_html(request):
    user = users.get_current_user()
    if user:
        watcher = Watcher.get_or_insert(user.user_id())
        website_list = db.get(watcher.websites)

        return render_to_response("websiteajax.html", {   
                        'website_list': website_list,
                        },)
    else:
        return HttpResponseRedirect(users.create_login_url("/websites/"))
        
        
def alarms(request):
    user = users.get_current_user()
    if user:
        thirty_days = datetime.now()-timedelta(days=30)
        
        watcher = Watcher.get_or_insert(user.user_id())           
        alert_q = AlertHistory.all()
        alert_q  = alert_q.filter('watcher =', watcher)
        alert_list = alert_q.filter('end_date >', thirty_days) 
        #order('-end_date')
        
        return render_to_response("alarms.html", {   
            'alert_list': alert_list,
            'user': user,
            'logout_url': users.create_logout_url("/"),
            },)

    else:
        return HttpResponseRedirect(users.create_login_url("/websites/"))
        
def verify_down(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        try:
            result = urlfetch.fetch(url, method='HEAD', deadline = 10, headers = {'Cache-Control' : 'max-age=30'} )
            code = result.status_code
        except:
            code = 0
            
        if code != 200:
            q = Website.all()
            q.filter("url =", url)
            website = q.get()
            website.status = 'Down'
            website.put()
            for watcher in website.members:
                alert = AlertHistory(watcher=watcher, website=website)
                alert.put()
                mail.send_mail(sender="Unmetric Monitoring <zephell@gmail.com>",
                  to=watcher.user.email(),
                  subject="URL Status Down",
                  body="""%s has just been marked as down.""" % website.url)
    return HttpResponse("OK")
    
def verify_up(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        try:
            result = urlfetch.fetch(url, method='HEAD', deadline = 5, headers = {'Cache-Control' : 'max-age=30'} )
            code = result.status_code
        except:
            code = 0
            
        if code == 200:
            q = Website.all()
            q.filter("url =", url)
            website = q.get()
            website.status = 'Up'
            website.put()
            for watcher in website.members:
                query = AlertHistory.all()
                query = query.filter('website =', website)
                query = query.filter('watcher =', watcher)
                query = query.filter('end_date =', None)
                alert = query.get()
                alert.end_date = datetime.now()
                alert.put()
                mail.send_mail(sender="Unmetric Monitoring <zephell@gmail.com>",
                  to=watcher.user.email(),
                  subject="URL Status Up",
                  body="""%s has just been marked as up.""" % website.url)
    return HttpResponse("OK")
    
def webthumb(request):
    if request.method == 'GET':
        url = request.GET.get('url')
        q = Website.all()
        q.filter("url =", url)
        website_obj = q.get()
        if website_obj.url_image:
            response = HttpResponse(website_obj.url_image)
            response['Content-Type'] = "image/png"
            return response
                
def probe_one_website(request):
    if request.method == 'GET':
        url = request.GET.get('url')
        q = Website.all()
        q.filter("url =", url)
        website_obj = q.get()
        
        try:
            result = urlfetch.fetch(url, method='HEAD', deadline = 6, headers = {'Cache-Control' : 'max-age=30'} )
            result_code = result.status_code
        except:
            result_code = 0

        if website_obj.status == 'Up' and result_code != 200:
            taskqueue.add(url='/verify_down/', params={'url': url})
        elif website_obj.status == 'Down' and result_code == 200:
            taskqueue.add(url='/verify_up/', params={'url': url})
        else:
            website_obj.status_code = result_code
            website_obj.probe_time = datetime.now()
            website_obj.put()
            
    return HttpResponse("OK")

def fix_website(request):
    website_list = Website.all()
    for site in website_list:
        try:
            delattr(site, 'au_time')
        except:
            pass
    return HttpResponse("OK")
    
def probe_all_websites(request):
    five_min = datetime.now()-timedelta(minutes=5)
    website_list = Website.all().filter('probe_time <', five_min) 
    
    rpcs = []
    for site in website_list:
        #url_list.append(site.url)
        rpc = urlfetch.create_rpc(deadline = 10)
        urlfetch.make_fetch_call(rpc, "http://unmetric.appspot.com/probe_one_website/?url=%s" % site.url, method='GET')
        rpcs.append(rpc)

    for rpc in rpcs:
        rpc.wait()
    
    return HttpResponse("OK") 

def probe_down_websites(request):
    website_list = Website.all().filter("status =", "Down") 
    rpcs = []
    for site in website_list:
        #url_list.append(site.url)
        rpc = urlfetch.create_rpc(deadline = 10)
        urlfetch.make_fetch_call(rpc, "http://unmetric.appspot.com/probe_one_website/?url=%s" % site.url, method='GET')
        rpcs.append(rpc)

    for rpc in rpcs:
        rpc.wait()
    
    return HttpResponse("OK") 
    
# I know the below is insanely stupid
def count_stats(request):
    website_list = Website.all()
    total = website_list.count(999999)
    
    web_obj = TotalHistory(num=total, status="Websites")
    web_obj.save()
    
    alert_list = AlertHistory.all()
    alert_total = alert_list.count(999999)
    
    alert_obj = TotalHistory(num=alert_total, status="Alerts")
    alert_obj.save()
    
    user_list = Watcher.all()
    user_total = user_list.count(999999)
    
    user_obj = TotalHistory(num=user_total, status="Users")
    user_obj.save()
    
    return HttpResponse("OK") 

def generate_csv(request, slug):
    import csv
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' % slug

    writer = csv.writer(response)
    
    if request.method == 'GET':
        q = Website.all()
        q.filter("slug =", slug)
        website_obj = q.get()

        alert_q = AlertHistory.all()
        alert_q = alert_q.filter('website =', website_obj)
        alert_list = alert_q.order("-end_date")
    
        for alert in alert_list:
            row = [alert.website.url, alert.start_date, alert.end_date]
            writer.writerow(row)
    

    return response



def mobile_api(request):
    try:
            # Get the db.User that represents the user on whose behalf the
            # consumer is making this request.
        user = oauth.get_current_user()
	return render_to_response("jsontest.html", {   

		    },)
    except oauth.OAuthRequestError, e:
	    # The request was not a valid OAuth request.
	    # ...
	return render_to_response("jsonfail.html", {   

		    },)


