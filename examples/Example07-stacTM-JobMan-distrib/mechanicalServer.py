import os
import sys
sys.path.extend(['.','..', '../..'])
from mupif import *
util.changeRootLogger('mechanical.log')
import argparse
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from mechanicalServerConfig import serverConfig
cfg = serverConfig(mode)

# locate nameserver
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run a daemon for jobMamager on this machine
daemon = pyroutil.runDaemon(
    host=cfg.server, port=cfg.serverPort, nathost=cfg.serverNathost, natport=cfg.serverNatport)

# Run job manager on a server
jobMan = simplejobmanager.SimpleJobManager2(
    daemon, ns, cfg.applicationClass, cfg.jobManName+'-ex07', cfg.portsForJobs, cfg.jobManWorkDir, os.getcwd(),
    'mechanicalServerConfig', mode, cfg.jobMan2CmdPath, cfg.maxJobs, cfg.socketApps)

pyroutil.runJobManagerServer(
    server=cfg.server,
    port=cfg.serverPort,
    nathost=cfg.serverNathost,
    natport=cfg.serverNatport,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    appName=cfg.jobManName+'-ex07',
    jobman=jobMan,
    daemon=daemon
)
