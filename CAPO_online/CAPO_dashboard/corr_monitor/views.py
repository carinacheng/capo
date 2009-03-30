# Create your views here.
from django.shortcuts import render_to_response, get_object_or_404
from CAPO_dashboard.corr_monitor.models import * 
from django.template import Context, loader
from django.http import HttpResponseRedirect, HttpResponse,HttpResponseNotFound
from django.core.urlresolvers import reverse
import math as m,numpy as np
from django.contrib import admin
import corr.plotdb
from django.forms import ModelForm
import pylab as pl


dbfilename = '/Users/danny/Work/radio_astronomy/Software/CAPO/CAPO_online/CAPO_dashboard/corr_monitor/corr.db'
vistablewidth = 500
rewire = {
   6: {'x': 8, 'y': 9},
   7: {'x':10, 'y':11},
   4: {'x': 4, 'y': 5},
   5: {'x': 6, 'y': 7},
   2: {'x': 0, 'y': 1},
   3: {'x': 2, 'y': 3},
   0: {'x':12, 'y':13},
   1: {'x':14, 'y':15},
}
class SettingsForm(ModelForm):
    """
    Defines a form used to set un-common settings.
    """
    class Meta:
        model = Setting
class DBForm(ModelForm):
    """
    Defines a form used to set the current data database
    """
    class Meta:
        model = Setting
        fields = ('refdb',)
class FilterForm(ModelForm):
    """
    Defines a form used to apply data filtering etc settings to dashboard
    """
    class Meta:
        model = Filter
class PlotSettingForm(ModelForm):
    """
    Defines a form used to set plotting variables
    """
    class Meta:
        model = PlotSetting
        exclude = ('visibility',)
#def select(request):
#    """
#    Create a new filter.
#    """
#    if request.method == 'POST':  #if data is submitted, process it.
#        form = FilterForm(request.POST)
#        if form.is_valid():
#            return HttpResponse(str(form.cleaned_data['id']))
##            form.save()       
##            return HttpResponseRedirect('/corr_monitor/filters/')
#    else: 
#        form = FilterForm()
#    return render_to_response('corr_monitor/select.html', {
#        'form':form,
#        })
def filter_detail(request,f_id=0):
    """
    Edit an existing Filter or create a new one.
    """
    if f_id==0:
        if request.method=='POST':
            form = FilterForm(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/corr_monitor/filters/')
        else:
            form = FilterForm()
            action = '/corr_monitor/filters/save/'
    
    else:
        try: filter = Filter.objects.get(id=f_id)
        except(Filter.DoesNotExist): 
            return HttpResponseRedirect('/corr_monitor/filters/add/')
        if request.method=='POST':
            form = FilterForm(request.POST,instance=filter)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/corr_monitor/filters/')
        else:
            form = FilterForm(instance=filter)
            action = '/corr_monitor/filters/'+str(f_id)+'/update/'
    return render_to_response('corr_monitor/filter_detail.html', {
        'form':form,
        'action':action
        })
    
def filters(request):
    """
    Displays a list of available filters. And some other stuff that I always
    want to be showing.
    """
    settings  = load_settings()
    #current_filter = Filter.objects.filter(id=settings.filter_id)
    filters = Filter.objects.exclude(id=settings.filter_id)
    return render_to_response('corr_monitor/filters.html', {
        'filters':filters,
        'current_filter':settings.filter
       })
       
def load_settings():
    setting,created = Setting.objects.get_or_create(lon='45',name='Default')
    return setting
def update_settings(request):
    s = load_settings()
    if request.method=='POST':
        form = DBForm(request.POST,instance=s)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/corr_monitor/')
    else:
        form = SettingsForm(instance=s)
    return render_to_response('corr_monitor/setting_detail.html',
       {'form':form})
    
def help(request):
    return render_to_response('corr_monitor/help.html')
        
def filter_toggle(request,f_id):
    """
    Toggles a filter in current settings.
    """
    #load setting
    setting = load_settings()
    if setting.filter_id==f_id:
        setting.filter_id=0
    else:
        setting.filter_id = f_id
    setting.save()
    return HttpResponseRedirect('/corr_monitor/filters/')  
             
def key2bl(old_key):
    """
    Re-do a dbm to match physical wiring. (eg correct_ script)
    """
    ants,pol = old_key.split(',')
    polA,polB = pol[0],pol[1]
    antA,antB = ants.split('-')
    if antA==antB and pol=='yx': return "","",True
    antA = str(rewire[int(antA)][polA])
    antB = str(rewire[int(antB)][polB])
    polA = polB = 'y'
    return antA+polA,antB+polB,False

def toggle_update_daemon(request,db_id):
    """
    Starts or stops daemon that updates database with db_id.
    """
    
    
def update(request,db_id=0):
    """
    Loads all visibility records from given filename.
    """
    #filename=dbfilename
    s = load_settings()
    if db_id==0: filename = s.refdb.filename
    else: filename = CorrDB.objects.get(pk=db_id).filename
    db = corr.plotdb.PlotDB(filename)
    keys = db.keys()
    keys.sort()
    html = ""
    for k in keys: 
        #find the auto-correlations:
        try: indx=k.index('-')
        except: continue
        #print 'Found - at index %i in key %s'%(indx,k)
        #print 'Comparing %s to %s.'%(k[0:indx],k[indx+1:-3])
        antA,antB,skip = key2bl(k)
        if skip:continue
        if (antA==antB): is_auto=1
        else: is_auto=0
        #No warnings are generated until the score has been computed.
        warning = Warning.objects.get(name="None")
        #chech for existing baselines
        try: 
            old_v = Visibility.objects.filter(antA=antA).get(antB=antB)
            oldid = old_v.id
        except(Visibility.DoesNotExist):oldid = None
        new_v = Visibility(
            baseline=k,
            antA = antA,
            antB = antB,
            is_auto=is_auto,
            score=0,   
            id=oldid)
        new_v.save()
        new_v.warning.add(warning)
        new_v.save()
        #print Visibility.objects.all()
        #html = html +"."+ bl
    return HttpResponseRedirect('/corr_monitor/')
    #return HttpResponse(html)   
   
def score(visibilities):
    """
    Compute scores of visibilities and create any necessary warnings.
    """
def get_vis(f=None):
    """
    Queries the visibility table applying filter in QuerySet f.
    TODO: support warnings.
    """

    v_string = "v = Visibility.objects.all()"
    
    if not f is None:            
        for k,d in f.values()[0].iteritems():
            if not d is None:
                if k is 'auto' and d:
                    v_string = v_string + ".extra(where=['antA=antB'])"
                if k is 'cross' and d:
                    v_string = v_string + ".extra(where=['antA<>antB'])"
                if k is 'antA':
                    v_string = v_string + ".filter(antA__contains="+str(d)+")"
                if k is 'antB':
                    v_string = v_string + ".filter(antB__contains="+str(d)+")"
                if k is 'polA':
                    v_string = v_string + ".filter(antA__contains="+str(d)+")"
                if k is 'polB':
                    v_string = v_string + ".filter(antB__contains="+str(d)+")"
    print v_string
    exec(v_string)
    return v
 
def index(request):
    s = load_settings()
    filter = Filter.objects.all().filter(id=s.filter_id)
    v = get_vis(f=filter)
 
    if v.count()>0:
        m2 = int(m.sqrt(float(v.count())))
        m1 = int(m.ceil(float(v.count()) / m2))
    else:
        m2 = 1
        m1 = 1
    tdwidth = str(vistablewidth/m1)+'px'
    n=0
    table = ""
    v.order_by('antA')#.order_by('antB')
    for i in range(m2):
        table =table + "<tr>"
        for j in range(m1):
           if n<v.count(): 
              classname = str(v[n].warning.all()[0].name)
              table = table + "<td class=\""+ classname +"\""
              table = table + " onmouseover= \"this.className="
              table = table + "'"+ classname +  " mouseborder'\" "
              table = table + " onmouseout = \"this.className='"+classname+"'\""
              table = table + "style=\"width:"+tdwidth
              table = table + "; height:"+tdwidth + "\" >"
              table = table + "<span style=\"font-size:10pt\">"
              table = table + "<a href=\"vis/"+str(v[n].id)+"\"/>"
              table = table + str(v[n].antA)
              table = table + "<br> "+str(v[n].antB)
              table = table + "</span></a>"
              table = table + "<br>"
#              table = table + str(v[n].score)
              table = table + "</td>"
              n +=1
        table = table + "</tr>"
    v.rows = table
    #select all baselines with warnings.name!=None
    w = Warning.objects.exclude(name__exact="None")
    dbform = DBForm(instance=s)
    print v[0].datetime
    return render_to_response('corr_monitor/main.html',
    {'settings': s,'visibilities':v,'warnings':w,
      'dbform':dbform,'time':v[0].datetime})

def adjust_plot(vis):
    """
    Modifies a figure plotting a single visibility. 
    Returns a PlotSetting object.
    """
    #get the plot setting corresponding to this guy
    pset,created =  vis.plotsetting_set.get_or_create(ymin=None)
    if not pset.ymax is None: 
        pl.ylim(ymax=float(pset.ymax))
    if not pset.ymin is None:
        pl.ylim(ymin=float(pset.ymin))
    if not pset.xmin is None:
        pl.xlim(xmin=float(pset.xmin))
    if not pset.xmax is None:
        pl.xlim(xmax=float(pset.xmax))
    
        #pl.title(str(pset.ymax))

    #... more settings
    return pset
                
def vis_detail(request, vis_id):
    """
    Look at a baseline in detail.
    """
    vis = get_object_or_404(Visibility,pk=vis_id)
    pl.figure()
    pset = adjust_plot(vis)
    messages = []
    if request.method=='POST':
        settingform = PlotSettingForm(request.POST,instance=pset)
        if settingform.is_valid():
            settingform.save()
            messages.append("Graph updated")
            return HttpResponseRedirect('/corr_monitor/vis/'+vis_id+'/')

    db = corr.plotdb.NumpyDB(dbfilename)
    dataseries = db.read(str(vis.baseline))
    outfile = '/corr_monitor/media/img/temp.png'
    temproot = '/Users/danny/Work/radio_astronomy/Software/CAPO/CAPO_online/CAPO_dashboard/templates'
    pl.plot(np.abs(dataseries))
    pl.grid()
    pl.ylabel('raw amplitude [V]')
    pset = adjust_plot(vis)
    pl.savefig(temproot+outfile,format='png')
    settingform=PlotSettingForm(instance=pset)
        
    return render_to_response('corr_monitor/vis_detail.html',
         {'vis' : vis,
         'graphs':(outfile,),
         'plotsetting_form':settingform,
         'messages':messages
         })
