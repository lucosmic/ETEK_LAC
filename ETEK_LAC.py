# ./LAC/ETEK_LAC.py

#EmergenTek LAC Implemtntation


import subprocess as sp
import re #regular expressions, searching strings

import threading #Threading, for computer-side feedback control
import time


class ETEK_LAC():
    '''EmergenTek Implementation of Actuonix LAC'''
    WRITE_CODES =  {"SET_ACCURACY":         0x01, 
                    "SET_RETRACT_LIMIT":    0x02, 
                    "SET_EXTEND_LIMIT":     0x03, 
                    "SET_MOVE_THRESH":      0x04, 
                    "SET_STALL_TIME":       0x05, 
                    "SET_PWM_THRESH":       0x06, 
                    "SET_DERIV_THRESH":     0x07, 
                    "SET_DERIV_MAX":        0x08, 
                    "SET_DERIV_MIN":        0x09, 
                    "SET_PWM_MAX":          0x0A, 
                    "SET_PWM_MIN":          0x0B, 
                    "SET_PROP_GAIN":        0x0C, 
                    "SET_DERIV_GAIN":       0x0D, 
                    "SET_AVG_RC":           0x0E, 
                    "SET_AVG_ADC":          0x0F, 
                    "GET_FEEDBACK":         0x10, 
                    "SET_POSITION":         0x20, 
                    "SET_SPEED":            0x21, 
                    "DISABLE_MANUAL":       0x30, 
                    "RESET":                0xFF}
    
    #TODO: Let's record the default settings from the Windows USB program.
    defaultSettings = {'ACCURACY':      0, 
                    'RETRACT_LIMIT':    0, 
                    'EXTEND_LIMIT':     1023, 
                    'MOVE_THRESH':      None, 
                    'STALL_TIME':       None, 
                    'PWM_THRESH':       None, 
                    'DERIV_THRESH':     None, 
                    'DERIV_MAX':        None, 
                    'DERIV_MIN':        None, 
                    'PWM_MAX':          None, 
                    'PWM_MIN':          None, 
                    'PROP_GAIN':        None, 
                    'DERIV_GAIN':       None, 
                    'AVG_RC':           None, 
                    'AVG_ADC':          None, 
                    'SPEED':            None}
    
    
    connectedLACs = []
    #Possible: Use the threading class to provide continuous feedback action. 
    #(See InRedox_Python/Titrator/Titrator_Code_v2/TitratorSensor.py for example)
    
    def __init__(self, length=100, rank=1, setSettings=False):
        '''Start the actuator. Length is 100mm by default. Rank is the address of the actuator. 
        Each object is an individual actuator. '''
        #Check that lac program is in /bin/
        
        #Check that the LAC is connected, also get current position
        try:
            self.currPos = sp.check_output(['lac','rank={0:d}'.format(int(rank)),'write=0x10'])
        except sp.CalledProcessError as e:
            print(e)
            raise e
        
        #Initialize the feedback thread
        ###threading.Thread.__init__(self)
        self.fbt = threading.Timer(0.01,self.runFeedback)
        
        #Setup the LAC
        self.length = length        #Length of this actuator
        self.rank = int(rank)       #Address of the actuator
        self.rankEQStr = 'rank={0:d}'.format(int(rank))
        if self.rank in self.connectedLACs:
            print('raise Warning("Duplicate Reference to a single LAC")')
        else:
            self.connectedLACs.append(self.rank)
        
        #Set Starting Settings
        self.settings = {}
        if setSettings is not None:
            if setSettings is True:
                self.settings = self.defaultSettings
            elif type(setSettings) == type(dict()):
                for k in setSettings:
                    if k in self.defaultSettings:
                        self.settings.update( {k:setSettings[k]} )
            #Disable Manual Settings (This was causing issues thus commented out and could be deleted)
            ##sp.check_output(['lac', 'write={}'.format(self._hexConvert(self.WRITE_CODES["DISABLE_MANUAL"])) ])
            #Set Settings
            self.set_settings(self.settings)
        
    def __repr__(self):
        '''Executed when calling repr(LAC_Object) or print(LAC_Object)'''
        return "ETEK_LAC #{0:d}, Length={1:d}mm, Position={2:0.2f}mm".format(
            self.rank,self.length,self.get_pos_mm())
    
    def __del__(self):
        print("Removed LAC #{}".format(self.rank))
        self.connectedLACs.remove(self.rank)
    
    def _hexConvert(self, number):
        '''Converts a hex number into a 4-character long string'''
        hexstr=hex(number)
        if len(hexstr)<4:
            hexstr = '0x0'+hexstr[-1]
        elif len(hexstr)>4:
            hexstr = '0xff'
        
        return hexstr
    
    def set_settings(self, settings=None):
        '''Set LAC settings.
        Input: A dict with keys matching the following:
        ACCURACY: 0(low width)-1023(full width) 
        RETRACT_LIMIT: 0 (no movement below this)
        EXTEND_LIMIT: 1023 (no movement above this)
        MOVE_THRESH: (speed)
        STALL_TIME: ms to wait before turning off
        PWM_THRESH: ()
        DERIV_THRESH: ()
        DERIV_MAX: ()
        DERIV_MIN: ()
        PWM_MAX: ()
        PWM_MIN: ()
        PROP_GAIN: ()
        DERIV_GAIN: ()
        AVG_RC: ()
        AVG_ADC: ()
        SPEED: ()
        '''
        output = []
        if settings==None:
            return
        else:
            for k in settings:
                if settings[k] == None:
                    continue
                sk=('SET_'+k)
                if sk in self.WRITE_CODES.keys():
                    print(k, settings[k])
                    try:
                        #oup = sp.check_output( ['lac', 'write=0x01,0'] )
                        #output.append( oup)
                        output.append(sp.check_output( ['lac', self.rankEQStr, 'write={},{}'.format( 
                            self._hexConvert(self.WRITE_CODES[sk]),settings[k] ) ] ))
                        self.settings.update({k:settings[k]})
                    except sp.CalledProcessError as e:
                        print(e)
                        print("Could not execute command ", sk)
        
        return output
        
        
    
    def write_raw(self, input):
        '''write_raw(["list","of","commands"])'''
        if type(input) == str:
            cmd=["lac"]
            for v in input.split(" "): 
                if v in self.WRITE_CODES.keys():
                    cmd.append( self._hexConvert(self.WRITE_CODES[v]) )
                else:
                    cmd.append(v) 
            try:
                output = sp.check_output(cmd)
            except:
                print("could not execute")
        
        elif type(input) ==list:
            if not input[0] == "lac":
                cmd = ['lac', self.rankEQStr]
                for v in input.split(" "): cmd.append(v) 
            else:
                cmd = input
            print(cmd)
            try:
                output = sp.check_output(cmd)
            except:
                print("could not execute")
                return None
        else:
            return None
        return output
    
    def set_pos(self, setpos, setspeed=None):
        '''Set position between 0 and 1023 (fully extended)'''
        #Data Validation
        setpos = min(1023, setpos)
        setpos = max(0, setpos)
        
        if setspeed is not None:
            #Data Validation for setspeed
            
            #Output Speed: Uncomment when data is validated (by Windows USB program). 
            #output = sp.check_output(['lac', 'write=0x21,{0:d}'.format(setspeed)])
            pass
        
        #Output LAC position at beginning of setting the position.
        output = sp.check_output(['lac', self.rankEQStr, 'write=0x20,{0:d}'.format(setpos)])
        self.setPos = setpos
        
        return int(re.search("\d+",output.decode('utf-8')).group())
    
    def set_pos_mm(self, setposmm, setspeed=None):
        '''Set position as a number of milimeters.'''
        if setspeed is not None:
            setspeed = setspeed/self.length*1023
        output = self.set_pos(int(setposmm/self.length*1023), setspeed)
        output = output/1023*self.length
        
        return output
    
    def get_pos(self):
        '''Get Position (0-1023)'''
        output = sp.check_output(['lac', self.rankEQStr, 'write=0x10'])
        self.currPos = int(re.search("\d+",output.decode('utf-8')).group())
        return self.currPos
    
    def get_pos_mm(self):
        output = self.get_pos()
        output = output/1023*self.length
        return output
    
    def stopFeedback(self):
        self.fbt.cancel()
        self.feedbackRunning = False
    
    def startFeedback(self,kp=3):
        '''Starts the feedback thread.Proportional constant kp is 3 by default.'''
        self.kp = kp
        self.fbt.start()
        ###self.start()
    
    def runFeedback(self):
        '''run the feedback thread'''
        self.feedbackRunning = True
        self.prevPos=self.get_pos()
        if not ('kp' in dir(self)):
            self.kp=1
        
        while self.feedbackRunning:
            diff = self.get_pos()-self.prevPos
            self.set_pos(self.currPos+diff*self.kp)
            self.prevPos = self.currPos
            time.sleep(0.01)
            
