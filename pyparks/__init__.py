
# coding: utf-8

# In[2]:


import requests
from datetime import datetime
import pandas as pd
from unidecode import unidecode


# In[3]:




class disney_park:
        

    def __init__(self):
        self.__API_BASE = "https://api.wdpro.disney.go.com/"
        self.tokendata = self.__get_tokendata()
        self.token = self.tokendata['access_token']
        self.expirtime = self.tokendata['expires_in']
        self.parkid = self.get_parkid()
        self.resortid = self.get_resortid()
        self.__headers = {
        'Accept-Language' : 'en_US',
        'User-Agent': 'UIEPlayer/2.1 iPhone OS 6.0.1',
        'Accept' : 'application/json;apiversion=1',
        'Authorization' : "BEARER "+str(self.token),
        'X-Conversation-Id' : 'WDPRO-MOBILE.MDX.CLIENT-PROD',
        'X-Correlation-ID' : str(datetime.now().timestamp())
        }
        self.rawwaitdata = self.__get_rawwaitdata()
        self.timeretrieved = self.__get_time()
        self.size = len(self.rawwaitdata['entries'])
        self.waitdata,self.names = self.__get_waitdata()
        self.__entertainment_indeces,self.__reverse_ent_indeces = self.__get_ent_indeces()
        self.waitdata_attractions = self.waitdata.iloc[:,self.__reverse_ent_indeces]
        self.waitdata_entertainement = self.waitdata.iloc[:,self.__entertainment_indeces]
        if self.can_get_fastpass(): 
            self.fastpass,self.__truefastpassindex = self.get_fastpass()
            self.fastpasstrue = self.fastpass.iloc[:,self.__truefastpassindex]
        self.isopen,self.__op_index = self.__get_isopen()
        self.openwaitdata = self.waitdata.iloc[:,self.__op_index]
        self.rawscheduledata = self.__get_rawscheduledata()
        self.todays_hours = self.get_scheduledata()

    
    
    def refresh(self):
        """Refreshes the information by reinitializing the object."""
        
        self.__init__()
        
        
    def __get_tokendata(self):
        """Grabs Auth Token"""
        TOKEN_URL = 'https://authorization.go.com/token?grant_type=assertion&assertion_type=public&client_id=WDPRO-MOBILE.MDX.WDW.ANDROID-PROD'
        r = requests.post(url = TOKEN_URL)
        data = r.json()
        return(data)
    
    def get_parkid(self):
        """Park ID provided by inherited class"""
        raise("Method Must Be Defined By Inherited Class")
        return(0)
        
    def get_resortid(self):
        """Resort ID provided by inherited class"""
        raise("Method Must Be Defined By Inherited Class")
        return(0)
    def __get_rawwaitdata(self):
        """Raw Wait Data Input to be used by other attributes and methods"""
        r = requests.get(url = self.__API_BASE+'facility-service/theme-parks/{}/wait-times'.format(self.parkid),headers=self.__headers)
        data = r.json()
        return(data)
    
    def __get_rawscheduledata(self,startDate =datetime.now().strftime('%Y-%m-%d'),endDate = False ):
        """Raw Schedule Data Input to be used by other attributes and methods"""
        if not endDate:
            endDate = startDate
        r = requests.get(url = self.__API_BASE + 'mobile-service/public/ancestor-activities-schedules/{};entityType=destination?filters=theme-park&startDate={}&endDate={}&region=us'.format(self.resortid,startDate,endDate),headers=self.__headers)
        data = r.json()
        return(data)
        
    def __get_time(self):
        """Grab time when accessing API"""
        time = datetime.now()
        return(time)
    
    def __get_waitdata(self):
        """Cleans Wait Data From Raw Wait Data"""
        rawdata = self.rawwaitdata
        names = []
        times = []
        for i in range(0,self.size):
            names.append(unidecode(rawdata['entries'][i]['name'].replace('"','').replace(' ','_').replace('–','_').replace("'",'').replace(':','_').replace('!','').replace(',','').replace('\xa0','').replace('.','').replace('&','and').replace('-','').replace('É','e').lower().strip()+ '_' + str(rawdata['entries'][i]['id']).split(';')[0]))
            try:
                times.append([rawdata['entries'][i]['waitTime']['postedWaitMinutes']])
            except KeyError:
                if rawdata['entries'][i]['waitTime']['status'] == "Down":
                    times.append([-1])
                elif rawdata['entries'][i]['waitTime']['status'] == "Operating":
                    times.append([0])
                else:
                    times.append([-2])

        data = dict(zip(names,times))
        data = pd.DataFrame.from_dict(data)
        data = data[names]
        Time = pd.Series([self.timeretrieved])
        data['mytime'] = Time
        return(data,names)
    
    def __get_ent_indeces(self):
        """Grabs Indeces of Entertainment (Also Returns Indeces of Attractions)"""
        types = []
        for i in range(0,len(self.rawwaitdata['entries'])):
            types.append(self.rawwaitdata['entries'][i]['type'])
            
        indeces = [i for i,x in enumerate(types) if x=='Entertainment']
        reverse_indeces= list(set(range(0,self.size)) - set(indeces))
        time_indeces = [self.size]
        indeces.extend(time_indeces)
        reverse_indeces.extend(time_indeces)
        return((indeces,reverse_indeces))
        
    def get_fastpass(self):
        """Extracts Fastpass Data from Raw Wait Data"""
        rawdata = self.rawwaitdata
        times = []
        indeces = []
        for i in range(0,self.size):
            if rawdata['entries'][i]['waitTime']['fastPass']['available']:
                try:
                    indeces.append(i)
                    times.append([int(rawdata['entries'][i]['waitTime']['fastPass']['startTime'].replace(':','')[:-2])])
                except:
                    times.append([-1])
            else:
                times.append([-2])
                

        data = dict(zip(self.names,times))
        data = pd.DataFrame.from_dict(data)
        data = data[self.names]
        Time = pd.Series([self.timeretrieved])
        data['mytime'] = Time
        time_indeces = [self.size]
        indeces.extend(time_indeces)
        return((data,indeces))
        
    def can_get_fastpass(self):
        """Pass False if Park Data does not include Fastpass"""
        raise(("Method Must Be Defined By Inherited Class"))
        
    def __get_isopen(self):
        """Grabs Status of Attractions/Entertainment (Operating Or Not), Also Returns Indices of Open Attractions/Entertainment"""
        rawdata = self.rawwaitdata
        operating_or_not = []
        op_index = []
        for i in range(0,self.size):
            if rawdata['entries'][i]['waitTime']['status'] == 'Operating':
                operating_or_not.append(['Operating'])
                op_index.append(i)
            elif rawdata['entries'][i]['waitTime']['status'] == 'Down':
                operating_or_not.append(['Down'])
                op_index.append(i)
            else:
                operating_or_not.append(['Closed'])

        data = dict(zip(self.names,operating_or_not))
        data = pd.DataFrame.from_dict(data)
        data = data[self.names]
        Time = pd.Series([self.timeretrieved])
        data['mytime'] = Time
        time_indeces = [self.size]
        op_index.extend(time_indeces)
        
        return(operating_or_not,op_index)
    
    def get_scheduledata(self,startDate = False,endDate = False):
        """Cleans Schedule Data, Can Be Used Seperately to Find Schedule Of Specified Range. startDate and endDate Format is string "YYYY-MM-DD" """
        if startDate:
            rawdata = self.__get_rawscheduledata(startDate=startDate,endDate = endDate)
        else:
            rawdata = self.rawscheduledata
        for i in range(0,len(rawdata['activities'])):
            if rawdata['activities'][i]['id'].split(';')[0] == str(self.parkid):
                rightdata = rawdata['activities'][i]['schedule']['schedules']
                
        for j in range(0,len(rightdata)):
            if rightdata[j]['type']=='Operating':
                tempdata = pd.DataFrame(rightdata[j],index=[0])
                data = tempdata

                    
        
        return(data.reset_index(drop=True))
                
            
        


# In[4]:


class Disneyland(disney_park):

    def get_parkcoord(self):
        return({'lat':33.8121,'lon':-117.9190})
        
    def get_parkid(self):
        return(330339)

        
    def get_resortid(self):
        return(80008297)
    
    def can_get_fastpass(self):
        return(True)

class CaliforniaAdventure(disney_park):
    def get_parkid(self):
        return(336894)

        
    def get_resortid(self):
        return(80008297)
    
    def can_get_fastpass(self):
        return(True)
    
class MagicKingdom(disney_park):
    
    def get_parkid(self):
        return(80007944)

        
    def get_resortid(self):
        return(80007798)
    
    def can_get_fastpass(self):
        return(True)

