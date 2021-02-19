import os
import sys
sys.path.extend(['..', '../..'])
from mupif import *
util.changeRootLogger('server.log')
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from Config import config
cfg = config(mode)

# locate nameserver
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)
# Run a daemon for jobManager on this machine
daemon = pyroutil.runDaemon(
    host=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport)

# Run job manager on a server
jobMan = simplejobmanager.SimpleJobManager2(
    daemon=daemon,
    ns=ns,
    appAPIClass=None,
    appName=cfg.jobManName,
    portRange=cfg.portsForJobs,
    jobManWorkDir=cfg.jobManWorkDir,
    serverConfigPath=os.getcwd(),
    serverConfigFile='serverConfig',
    serverConfigMode=mode,
    jobMan2CmdPath=cfg.jobMan2CmdPath,
    maxJobs=cfg.maxJobs,
    jobMancmdCommPort=cfg.socketApps
)

pyroutil.runJobManagerServer(
    server=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport, nshost=cfg.nshost,
    nsport=cfg.nsport, appName=cfg.jobManName, jobman=jobMan, daemon=daemon)
