#!/usr/bin/env python3
import sys
sys.path.extend(['..', '../../..'])
from mupif import *
import jsonpickle
import time  # for sleep
import logging
log = logging.getLogger()
import mupif.Physics.PhysicalQuantities as PQ

#
# Expected response from operator: E-mail with "CSJ01" (workflow + jobID)
# in the subject line, message body: json encoded dictionary with 'Operator-results' key, e.g.
# {"Operator-results": 3.14}
#


class EmailAPI(Model.Model):
    """
    Simple application API that involves operator interaction
    """
    def __init__(self, file):
        super(EmailAPI, self).__init__(file)
        # note: "From" should correspond to destination e-mail
        # where the response is received (Operator can reply to the message)
        self.operator = operatorUtil.OperatorEMailInteraction(From='appAPI@gmail.com',
                                                              To='operator@gmail.com',
                                                              smtpHost='smtp.something.com',
                                                              imapHost='imap.gmail.com',
                                                              imapUser='appAPI')
        self.inputs = {}
        self.outputs = {}
        self.key = 'Operator-results'

    def initialize(self, file='', workdir='', metaData={}, validateMetaData=True, **kwargs):
        MD = {
            'Name': 'Email operator application',
            'ID': 'N/A',
            'Description': 'Sending email with input and receiving email with results',
            'Physics': {
                'Type': 'Other',
                'Entity': 'Other'
            },
            'Solver': {
                'Software': 'Unknown',
                'Language': 'Unknown',
                'License': 'Unknown',
                'Creator': 'Unknown',
                'Version_date': '02/2019',
                'Type': 'Summator',
                'Documentation': 'Nowhere',
                'Estim_time_step_s': 1,
                'Estim_comp_time_s': 0.01,
                'Estim_execution_cost_EUR': 0.01,
                'Estim_personnel_cost_EUR': 0.01,
                'Required_expertise': 'None',
                'Accuracy': 'Unknown',
                'Sensitivity': 'Unknown',
                'Complexity': 'Unknown',
                'Robustness': 'Unknown'
            },
            'Inputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_CumulativeConcentration', 'Name': 'Concentration', 'Description': 'Concentration', 'Units': 'kg/m**3', 'Origin': 'Simulated', 'Required': True}],
            'Outputs': [
                {'Type': 'mupif.Property', 'Type_ID': 'mupif.PropertyID.PID_Demo_Value', 'Name': 'Demo value',
                 'Description': 'Demo value', 'Units': 'dimensionless', 'Origin': 'Simulated'}]
        }
        self.updateMetadata(MD)
        super(EmailAPI, self).initialize(file, workdir, metaData, validateMetaData, **kwargs)

    def setProperty(self, property, objectID=0):
        # remember the mapped value
        self.inputs[str(property.propID)] = property
        self.inputs[self.key] = 0.0

    def getProperty(self, propID, time, objectID=0):
        md = {
            'Execution': {
                'ID': self.getMetadata('Execution.ID'),
                'Use_case_ID': self.getMetadata('Execution.Use_case_ID'),
                'Task_ID': self.getMetadata('Execution.Task_ID')
            }
        }
        if self.outputs:
            # unpack & process outputs (expected json encoded data)
            if propID == PropertyID.PID_Demo_Value:
                if self.key in self.outputs:
                    value = float(self.outputs[self.key])
                    log.info('Found key %s with value %f' % (self.key, value))
                    return Property.ConstantProperty(value, propID, ValueType.Scalar, PQ.getDimensionlessUnit(), time, 0, metaData=md)
                else:
                    log.error('Not found key %s in email' % self.key)
                    return None
            
    def solveStep(self, tstep, stageID=0, runInBackground=False):
        # send email to operator, pack json encoded inputs in the message
        # note workflow and job IDs will be available in upcoming MuPIF version
        self.operator.contactOperator("CS", "J01", jsonpickle.encode(self.inputs))
        responseReceived = False
        # check for response and repeat until received
        while not responseReceived:
            # check response and receive the data
            responseReceived, operatorOutput = self.operator.checkOperatorResponse("CS", "J01")
            # print(responseReceived, operatorOutput.splitlines()[0])
            if responseReceived:
                try:
                    self.outputs = jsonpickle.decode(operatorOutput.splitlines()[0])  # pick up only dictionary to new line
                except Exception as e:
                    log.error(e)
                log.info("Received response from operator %s" % self.outputs)
            else:
                time.sleep(60)  # wait
            
    def getCriticalTimeStep(self):
        return PQ.PhysicalQuantity(1.0, 's')


#################################################
# demo code
#################################################
# create instance of application API
app = EmailAPI(None)
try:
    executionMetadata = {
        'Execution': {
            'ID': '1',
            'Use_case_ID': '1_1',
            'Task_ID': '1'
        }
    }
    
    app.initialize(metaData=executionMetadata)

    # CumulativeConcentration property on input
    p = Property.ConstantProperty(0.1, PropertyID.PID_CumulativeConcentration, ValueType.Scalar, 'kg/m**3')
    # set concentration as input
    app.setProperty(p)
    # solve (involves operator interaction)
    tstep = TimeStep.TimeStep(0.0, 0.1, 1.0, 's', 1)
    app.solveStep (tstep)
    # get result of the simulation
    r = app.getProperty(PropertyID.PID_Demo_Value, tstep.getTime())
    log.info("Application API return value is %f", r.getValue())
    # terminate app

except Exception as e:
    log.error(e)
finally:
    app.terminate()
