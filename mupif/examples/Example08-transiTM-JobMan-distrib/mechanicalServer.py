# Mechanical server for nonstationary problem
import os
import sys
import logging
import argparse
sys.path.extend(['..', '../../..'])
from mupif import *
import models
# Read int for mode as number behind '-m' argument: 0-local (default), 1-ssh, 2-VPN
mode = argparse.ArgumentParser(parents=[util.getParentParser()]).parse_args().mode
from Config import config

cfg = config(mode)
log = logging.getLogger()
util.changeRootLogger('mechanical.log')

# locate nameserver
ns = pyroutil.connectNameServer(nshost=cfg.nshost, nsport=cfg.nsport)

# Run a daemon. It will run even the port has DROP/REJECT status. The connection from a client is then impossible.
# daemon = pyroutil.runDaemon(host=cfg.server3, port=cfg.serverPort3)

mechanical = models.mechanical()
# mechanical.initialize('..'+os.path.sep+'Example06-stacTM-local'+os.path.sep+'inputM10.in', '.')

pyroutil.runAppServer(
    server=cfg.server3,
    port=cfg.serverPort3,
    natport=None,
    nathost=None,
    nshost=cfg.nshost,
    nsport=cfg.nsport,
    appName='mechanical-ex08',
    app=mechanical
)
