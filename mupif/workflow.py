# 
#           MuPIF: Multi-Physics Integration Framework 
#               Copyright (C) 2010-2015 Borek Patzak
# 
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, 
# Boston, MA  02110-1301  USA
#

import os
import Pyro5
import time as timeTime
from . import model
from . import timestep
from . import units
import copy
import logging

log = logging.getLogger()

WorkflowSchema = copy.deepcopy(model.ModelSchema)
del WorkflowSchema["properties"]["Solver"]
del WorkflowSchema["properties"]["Physics"]
WorkflowSchema["properties"].update({
    "Dependencies": {  # This i automatically generated according to self._models List.
        "type": "array",  # List of contained models/workflows
        "items": {
            "type": "object",  # Object supplies a dictionary
            "properties": {
                "Label": {"type": "string"},  # Explicit label, given to the model/workflow by its parent workflow.
                "Name": {"type": "string"},  # Obtained automatically from Model metadata.
                "ID": {"type": ["string", "integer"]},  # Obtained automatically from Model metadata.
                "Version_date": {"type": "string"},  # Obtained automatically from Model metadata.
                "Type": {"type": "string", "enum": ["Model", "Workflow"]},  # Filled automatically.
                "Dependencies": {"type": "array"}  # Object supplies a dictionary
            },
            "required": ["Name", "ID", "Version_date", "Type"]
        }
    }
})
WorkflowSchema["required"] = ["Name", "ID", "Description", "Dependencies", "Execution", "Inputs", "Outputs"]


@Pyro5.api.expose
class Workflow(model.Model):
    """
    An abstract class representing a workflow and its interface (API).

    The purpose of this class is to represent a workflow, its abstract services for data exchange and steering.
    This interface has to be implemented/provided by any workflow. The Workflow class inherits from Application
    allowing to treat any workflow as model(application) in high-level workflow.

    .. automethod:: __init__
    """
    def __init__(self, *, metadata={}):
        """
        Constructor. Initializes the workflow

        :param dict metadata: Optionally pass metadata.
        """
        super().__init__(metadata=metadata)

        self.workflowMonitor = None  # No monitor by default
        self.targetTime = None
        self._models = {}

    def initialize(self, files=[], workdir='', targetTime=0.*units.Q.s, metadata={}, validateMetaData=True):
        """
        Initializes application, i.e. all functions after constructor and before run.
        
        :param list of str files: Name of file
        :param str workdir: Optional parameter for working directory
        :param PhysicalQuantity targetTime: target simulation time
        :param dict metadata: Optional dictionary used to set up metadata (can be also set by setMetadata() )
        :param bool validateMetaData: Defines if the metadata validation will be called
        """
        self.generateMetadataModelRefsID()
        self.updateMetadata(metadata)

        # print (targetTime)
        if isinstance(targetTime,units.Quantity):
            self.targetTime = targetTime
        else:
            raise TypeError('targetTime is not Quantity')
        
        self.files = files
        if workdir == '':
            self.workDir = os.getcwd()
        else:
            self.workDir = workdir

        if validateMetaData:
            self.validateMetadata(WorkflowSchema)

    def solve(self, runInBackground=False):
        """ 
        Solves the workflow.

        The default implementation solves the problem
        in series of time steps using solveStep method (inheritted) until the final time is reached.

        :param bool runInBackground: optional argument, default False. If True, the solution will run in background (in separate thread or remotely).

        """
        self.setMetadata('Status', 'Running')
        self.setMetadata('Progress', 0.)

        time = 0.*units.U.s
        timeStepNumber = 0
        
        while abs(time.inUnitsOf('s').getValue()-self.targetTime.inUnitsOf('s').getValue()) > 1.e-6:
            dt = self.getCriticalTimeStep()
            time = time+dt
            if time > self.targetTime:
                time = self.targetTime
            timeStepNumber = timeStepNumber+1
            istep = timestep.TimeStep(time=time, dt=dt, targetTime=self.targetTime, number=timeStepNumber)
        
            log.debug("Step %g: t=%g dt=%g" % (timeStepNumber, time.inUnitsOf('s').getValue(), dt.inUnitsOf('s').getValue()))

            # Estimate progress
            self.setMetadata('Progress', 100*time.inUnitsOf('s').getValue()/self.targetTime.inUnitsOf('s').getValue())
            
            self.solveStep(istep)
            self.finishStep(istep)
        self.setMetadata('Status', 'Finished')
        self.setMetadata('Date_time_end', timeTime.strftime("%Y-%m-%d %H:%M:%S", timeTime.gmtime()))
        self.terminate()

    def getAPIVersion(self):
        """
        :return: Returns the supported API version
        :rtype: str, int
        """
    def getApplicationSignature(self):
        """
        Get application signature.

        :return: Returns the application identification
        :rtype: str
        """
        return 'Workflow'
    
    def updateStatus(self, status, progress=0):
        """
        Updates the workflow status. The status is submitted to workflow monitor. The self.workflowMonitor
        should be (proxy) to workflowManager
        :param str status: string describing the workflow status (initialized, running, failed, finished)
        :param int progress: integer number indicating execution progress (in percent)
        """
        # pyroutil.connectNameServer(nshost, nsport, hkey)
        # try:
        #     uri = ns.lookup(workflowMonitorName)
        #     workflowMonitor = Pyro5.api.Proxy(uri)
        # except Exception as e:
        #     log.error("Cannot find workflow monitor")
        #     return # do not raise, silently continue without updating status

        if self.workflowMonitor:
            date = timeTime.strftime("%d %b %Y %H:%M:%S", timeTime.gmtime())
            # metadata = {workflowmonitor.WorkflowMonitorKeys.Status: status,
            # workflowmonitor.WorkflowMonitorKeys.Progress: progress,
            # workflowmonitor.WorkflowMonitorKeys.Date: date}
            metadata = {'WorkflowMonitor.Status': status,
                        'WorkflowMonitor.Progress': progress,
                        'WorkflowMonitor.Date': date}
            
            try:
                self.workflowMonitor.updateMetadata(self.getMetadata('WorkflowMonitor.ComponentID'), metadata)
                # could not use nameserver metadata capability, as this requires workflow to be registered
                # thus Pyro daemon is required

                log.debug(
                    self.getMetadata('WorkflowMonitor.ComponentID') + ": Updated status to " + status + ", progress=" +
                    str(progress)
                )
            except Exception as e:
                log.exception("Connection to workflow monitor broken")
                raise e

    def registerModel(self, mmodel, label=None):
        """
        :param model.Model or model.RemoteModel or Workflow model:
        :param str or None label: Explicit label of the model/workflow, given by the parent workflow.
        """
        if isinstance(mmodel, (Workflow, model.Model, model.RemoteModel, Pyro5.api.Proxy)):
            if label is None:
                i = 0
                while label in self.getListOfModelLabels() or i == 0:
                    i += 1
                    label = "label_%d" % i

            if label not in self.getListOfModelLabels():
                self._models.update({label: mmodel})
            else:
                raise KeyError("Given model label already exists.")
        else:
            raise TypeError("Parameter model should be instance of Workflow, Model, RemoteModel or Pyro5.api.Proxy.")

    def getDictOfModels(self):
        """
        :rtype: dict[model.Model, model.RemoteModel, Workflow]
        """
        return self._models.copy()

    def getListOfModels(self):
        """
        :rtype: list[model.Model, model.RemoteModel, Workflow]
        """
        return iter(self.getDictOfModels().values())

    def getListOfModelLabels(self):
        """
        :rtype: list of str
        """
        return iter(self.getDictOfModels().keys())

    def printListOfModels(self):
        print()
        print("List of child models:")
        print([m.__class__.__name__ for m in self.getListOfModels()])
        print()

    def generateMetadataModelRefsID(self):
        dependencies = []
        for key_name, mmodel in self.getDictOfModels().items():
            if isinstance(mmodel, (model.Model, Workflow, model.RemoteModel)):
                # Temporary fix due to compatibility
                if not mmodel.hasMetadata('Version_date') and not isinstance(model, Workflow):
                    if mmodel.hasMetadata('Solver.Version_date'):
                        mmodel.setMetadata('Version_date', mmodel.getMetadata('Solver.Version_date'))

                md_name = mmodel.getMetadata('Name') if mmodel.hasMetadata('Name') else ''
                md_id = mmodel.getMetadata('ID') if mmodel.hasMetadata('ID') else ''
                md_ver = mmodel.getMetadata('Version_date') if mmodel.hasMetadata('Version_date') else ''

                m_r_id = {
                    'Label': str(key_name),
                    'Name': md_name,
                    'ID': md_id,
                    'Version_date': md_ver,
                    'Type': 'Workflow' if isinstance(mmodel, Workflow) else 'Model'
                }
                if isinstance(mmodel, Workflow):
                    m_r_id.update({'Dependencies': mmodel.getMetadata('Dependencies')})
                dependencies.append(m_r_id)

        self.setMetadata('Dependencies', dependencies)
