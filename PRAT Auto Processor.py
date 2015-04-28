__author__ = 'Corwin'


import matlab.engine
import time


engine = matlab.engine.start_matlab()
async = engine.PRAT_Processor('E:\SEQ Files', 'E:\OUTCSV', async=True)
print "Initialized matlab"

while not async.done():
    print "Processing"
    time.sleep(1)

print "Finished processing"