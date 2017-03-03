# This script starts a server for Pyro4 on this machine with Application2
# Works with Pyro4 version 4.28
# Tested on Ubuntu 14.04 and Win XP
# Vit Smilauer 03/2017, vit.smilauer (et) fsv.cvut.cz

# If firewall is blocking daemonPort, run on Ubuntu
# sudo iptables -A INPUT -p tcp -d 0/0 -s 0/0 --dport 44382 -j ACCEPT

from __future__ import print_function, division

mode = 1 #Communication type 1=local(default), 2=VPN, 3=ssh tunnel

import sys
import socket
sys.path.append('..')

if mode==2:
    import conf_vpn as cfg
else:
    import conf as cfg

import Pyro4
from mupif import *
import mupif

@Pyro4.expose
class application2(Application.Application):
    """
    Simple application that computes an arithmetical average of mapped property
    """
    def __init__(self, file):
        super(application2, self).__init__(file)
        self.value = 0.0
        self.count = 0.0
        self.contrib = 0.0
    def getProperty(self, propID, time, objectID=0):
        if (propID == PropertyID.PID_CumulativeConcentration):
            return Property.Property(self.value/self.count, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, time, propID, 0)
        else:
            raise APIError.APIError ('Unknown property ID')
    def setProperty(self, property, objectID=0):
        if (property.getPropertyID() == PropertyID.PID_Concentration):
            # remember the mapped value
            self.contrib = property.getValue()
        else:
            raise APIError.APIError ('Unknown property ID')
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        mupif.log.debug("Solving step: %d %f %f" % (tstep.number, tstep.time, tstep.dt) )
        # here we actually accumulate the value using value of mapped property
        self.value=self.value+self.contrib
        self.count = self.count+1

    def getCriticalTimeStep(self):
        return 1.0

if mode!=3: #set NATport=port and local IP
    cfg.server = cfg.serverNathost
    cfg.serverNatport = cfg.serverPort

app2 = application2("/dev/null")

PyroUtil.runAppServer(cfg.server, cfg.serverPort, cfg.serverNathost, cfg.serverNatport, cfg.nshost, cfg.nsport, cfg.appName, cfg.hkey, app=app2)
