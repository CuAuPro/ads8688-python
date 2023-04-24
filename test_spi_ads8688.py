import wiringpi as wp
import time
from drivers import ads8688
#wiringpi.wiringPiSetup()      # For sequential pin numbering

adc = ads8688.ADS8688(bus=1, device=1, cs_pin=2, freq=100000)
adc.reset() # reset
adc.setGlobalRange(ads8688.R6)  # set range for all channels

##################################################
#               READING MANUAL CH0
##################################################
val = adc.manualChannel(0)
for i in range(5):
    time.sleep(0.1)
    val = adc.noOp()
    val = round(adc.raw2volt(val, ads8688.R6),4)
    print("Manual CH0: {}".format(val))


##################################################
#               READING MANUAL CH1
##################################################
val = adc.manualChannel(1)
for i in range(5):
    time.sleep(0.1)
    val = adc.noOp()
    val = round(adc.raw2volt(val, ads8688.R6),4)
    print("Manual CH1: {}".format(val))

##################################################
#               READING AUTO SEQUENCE CH0, CH1
##################################################
adc.setChannelSPD(0b00000011)
adc.autoRst()           # reset auto sequence

for i in range(5):
    vals = []
    time.sleep(0.1)
    for j in range(2):  
        val = adc.noOp()
        val = round(adc.raw2volt(val, ads8688.R6),4)
        vals.append(val)
    print("AUTO CH0, CH1: {}".format(vals))

##################################################
#               READING ALL CHANNELS
##################################################
adc.setChannelSPD(0b11111111)
adc.autoRst()           # reset auto sequence
for i in range(5):
    time.sleep(0.1)
    vals = []
    for i in range(adc.nr_channels):
        val = adc.noOp()
        val = round(adc.raw2volt(val, ads8688.R6),4)
        vals.append(val)
    print("AUTO ALL CH: {}".format(vals))
    #print(val)
