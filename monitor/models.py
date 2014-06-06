from google.appengine.ext import db
from django import forms
from google.appengine.ext.db import djangoforms

attrs_dict = { 'class': 'norm_required' }

class Watcher(db.Model):
    user = db.UserProperty()
    mobile = db.PhoneNumberProperty()
    code = db.StringProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    websites = db.ListProperty(db.Key)
    ports = db.ListProperty(db.Key)
    wgets = db.ListProperty(db.Key)
    
class TotalHistory(db.Model):
    num = db.IntegerProperty()
    status = db.StringProperty(
        choices=('Users', 'Websites', 'Alerts'))
    date = db.DateTimeProperty(auto_now_add=True)
                                   
class Port(db.Expando):
    ip_addr = db.LinkProperty('IP to monitor')
    port_num = db.IntegerProperty()
    status = db.StringProperty(
        choices=('Up', 'Down', 'Flap'))
    status_code = db.IntegerProperty()
    probe_time = db.DateTimeProperty()
    webserver_type = db.StringProperty(default=None)

    @property
    def members(self):
      return Watcher.gql("WHERE ports = :1", self.key())

class Probe(db.Model):
    location = db.StringProperty(
        choices=('au', 'us', 'uk'))
    ttlb = db.IntegerProperty()
    port = db.ReferenceProperty(Port,
            collection_name='port')
                                   
class Website(db.Expando):
    url = db.LinkProperty('Website To Monitor')
    slug = db.StringProperty()
    status = db.StringProperty(
        choices=('Up', 'Down', 'Flap'))
    status_code = db.IntegerProperty()
    probe_time = db.DateTimeProperty()
    webserver_type = db.StringProperty(default=None)
    os_type = db.StringProperty(default=None)
    
    @property
    def members(self):
      return Watcher.gql("WHERE websites = :1", self.key())
      
class AlertHistory(db.Model):
    watcher = db.ReferenceProperty(Watcher)
    website = db.ReferenceProperty(Website)
    start_date = db.DateTimeProperty(auto_now_add=True)
    end_date = db.DateTimeProperty()

class DowntimeHistory(db.Model):
    website = db.ReferenceProperty(Website)
    num = db.IntegerProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    
class Wget(db.Expando):
    name = db.StringProperty()
    slug = db.StringProperty()
    api_code = db.StringProperty()
    start_time = db.TimeProperty()
    end_time = db.TimeProperty()
    dow = db.StringListProperty()
        
    @property
    def members(self):
      return Watcher.gql("WHERE wgets = :1", self.key())
      
class WgetCheck(db.Model):
    wget = db.ReferenceProperty(Wget)
    check_date = db.DateTimeProperty(auto_now_add=True)
    status = db.StringProperty(default="OK")
    
# And some forms
class WebsiteForm(forms.Form):
    url = forms.URLField(required=True, label="Website to monitor", initial='http://')

class WgetForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs=attrs_dict), max_length=50, label="Backup Name")
    start_time = forms.TimeField(widget=forms.TextInput(attrs=attrs_dict), label="Start backup after")
    end_time = forms.TimeField(widget=forms.TextInput(attrs=attrs_dict), label="End backup before")
    dow = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                        choices=(
                                  ("sun", "Sunday"),
                                  ("mon", "Monday"),
                                  ("tue", "Tuesday"),
                                  ("wed", "Wednesday"),
                                  ("thr", "Thursday"),
                                  ("fri", "Friday"),
                                  ("sat", "Saturday"),
                                 ), label="Day of the week")
     
