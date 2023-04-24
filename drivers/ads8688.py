import spidev
import wiringpi as wp
import time
# COMMAND REGISTER MAP --------------------------------------------------------------------------------------------

NO_OP     = 0x00  # Continue operation in previous mode
STDBY     = 0x82  # Device is placed into standby mode
PWR_DN    = 0x83  # Device is powered down
RST       = 0x85  # Program register is reset to default
AUTO_RST  = 0xA0  # Auto mode enabled following a reset
MAN_Ch_0  = 0xC0  # Channel 0 input is selected
MAN_Ch_1  = 0xC4  # Channel 1 input is selected
MAN_Ch_2  = 0xC8  # Channel 2 input is selected
MAN_Ch_3  = 0xCC  # Channel 3 input is selected
MAN_Ch_4  = 0xD0  # Channel 4 input is selected
MAN_Ch_5  = 0xD4  # Channel 5 input is selected
MAN_Ch_6  = 0xD8  # Channel 6 input is selected
MAN_Ch_7  = 0xDC  # Channel 7 input is selected
MAN_AUX   = 0xE0  # AUX channel input is selected

# PROGRAM REGISTER MAP -------------------------------------------------------------------------------------------

# AUTO SCAN SEQUENCING CONTROL
AUTO_SEQ_EN   = 0x01  # Auto Sequencing Enable: default 0xFF - bitX to enable chX
CH_PWR_DN     = 0x02  # Channel Power Down: default 0x00 - bitX to power down chX

# DEVICE FEATURES SELECTION CONTROL
FT_SEL        = 0x03  # Feature Select: default 0x00
                            # bit 7-6 for daisy chain ID, bit 4 for ALARM feature, bit 2-0 SDO data format bits

# RANGE SELECT REGISTERS
RG_Ch_0       = 0x05   # Channel 0 Input Range: default 0x00 - bit 3-0 to select range
RG_Ch_1       = 0x06   # Channel 1 Input Range: default 0x00 - bit 3-0 to select range
RG_Ch_2       = 0x07   # Channel 2 Input Range: default 0x00 - bit 3-0 to select range
RG_Ch_3       = 0x08   # Channel 3 Input Range: default 0x00 - bit 3-0 to select range
RG_Ch_4       = 0x09   # Channel 4 Input Range: default 0x00 - bit 3-0 to select range
RG_Ch_5       = 0x0A   # Channel 5 Input Range: default 0x00 - bit 3-0 to select range
RG_Ch_6       = 0x0B   # Channel 6 Input Range: default 0x00 - bit 3-0 to select range
RG_Ch_7       = 0x0C   # Channel 7 Input Range: default 0x00 - bit 3-0 to select range

# ALARM FLAG REGISTERS (Read-only)
ALARM_OVERVIEW = 0x10  # ALARM Overview Tripped Flag
ALARM_CH0_TRIPPED_FLAG = 0x11  # ALARM Ch 0-3 Tripped-Flag
ALARM_CH0_ACTIVE_FLAG = 0x12  # ALARM Ch 0-3 Active-Flag
ALARM_CH4_TRIPPED_FLAG = 0x13  # ALARM Ch 4-7 Tripped-Flag
ALARM_CH4_ACTIVE_FLAG = 0x14  # ALARM Ch 4-7 Active-Flag

# ALARM THRESHOLD REGISTERS
CH0_HYST = 0x15  # Ch 0 Hysteresis
CH0_HT_MSB = 0x16  # Ch 0 High Threshold MSB
CH0_HT_LSB = 0x17  # Ch 0 High Threshold LSB
CH0_LT_MSB = 0x18  # Ch 0 Low Threshold MSB
CH0_LT_LSB = 0x19  # Ch 0 Low Threshold LSB
# ... CHx register address are Ch0 + 5x

# COMMAND READ BACK (Read-Only)
CMD_READBACK = 0x3F  # Command Read Back

# SPECIFIC VALUES -------------------------------------------------------------------------------------------

# RANGE SELECTION
R0 = 0x00  # Input range to -2.5/+2.5           *Vref   +/- 10.24V
R1 = 0x01  # Input range to -1.25/+1.25         *Vref   +/-  5.12V
R2 = 0x02  # Input range to -0.625/+0.625       *Vref   +/-  2.56V
R3 = 0x03  # Input range to -0.3125/+0.3125     *Vref   +/-  1.28V
R4 = 0x0B  # Input range to -0.15625/+0.15625   *Vref   +/-  0.64V
R5 = 0x05  # Input range to +2.5                *Vref   10.24V
R6 = 0x06  # Input range to +1.25               *Vref    5.12V
R7 = 0x07  # Input range to +0.625              *Vref    2.56V
R8 = 0x0F  # Input range to +0.3125             *Vref    1.28V

# OPERATION MODES
MODE_IDLE = 0
MODE_RESET = 1
MODE_STANDBY = 2
MODE_POWER_DN = 3
MODE_PROG = 4
MODE_MANUAL = 5
MODE_AUTO = 6
MODE_AUTO_RST = 7

class ADS8688:
    def __init__(self, bus=1, device=1, cs_pin=10, vref=4.096, freq=100000):
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.cs_pin = cs_pin
        self.nr_channels = 8
        wp.wiringPiSetup()

        wp.pinMode(self.cs_pin, wp.GPIO.OUTPUT)

        self.spi.mode = 0b00
        self.spi.max_speed_hz = freq
        #self.spi.cshigh = True
        #self.spi.lsbfirst = False
        #self.spi.no_cs = False
        #self.spi.threewire = False
        self.spi.bits_per_word = 8
        #self.spi.loop = False
        
        self.mode = MODE_IDLE
        self.vref = vref
        self.feature = 0

    def __del__(self):
        self.spi.close()
        
    #--------------------------------------------------
    def noOp(self):
        return self.cmdRegister(NO_OP)

    def standBy(self):
        return self.cmdRegister(STDBY)

    def powerDown(self):
        return self.cmdRegister(PWR_DN)

    def reset(self):
        self.mode = MODE_RESET
        return self.cmdRegister(RST)

    def autoRst(self):
        self.mode = MODE_AUTO_RST
        return self.cmdRegister(AUTO_RST)
    
    def manualChannel(self, ch):
        if ch == 0:
            reg = MAN_Ch_0
        elif ch == 1:
            reg = MAN_Ch_1
        elif ch == 2:
            reg = MAN_Ch_2
        elif ch == 3:
            reg = MAN_Ch_3
        elif ch == 4:
            reg = MAN_Ch_4
        elif ch == 5:
            reg = MAN_Ch_5
        elif ch == 6:
            reg = MAN_Ch_6
        elif ch == 7:
            reg = MAN_Ch_7
        elif ch == 8:
            reg = MAN_AUX
        else:
            reg = MAN_Ch_0
        self.mode = MODE_MANUAL
        return self.cmdRegister(reg)
    
    #--------------------------------------------------
    def setChannelSPD(self, flag):
        self.setChannelSequence(flag)
        self.setChannelPowerDown(~flag)

    def setChannelSequence(self, flag):
        self.writeRegister(AUTO_SEQ_EN, flag)

    def setChannelPowerDown(self, flag):
        self.writeRegister(CH_PWR_DN, flag)

    def getChannelSequence(self):
        return self.readRegister(AUTO_SEQ_EN)

    def getChannelPowerDown(self):
        return self.readRegister(CH_PWR_DN)

    def getChannelRange(self, ch):
        reg = {
            0: RG_Ch_0,
            1: RG_Ch_1,
            2: RG_Ch_2,
            3: RG_Ch_3,
            4: RG_Ch_4,
            5: RG_Ch_5,
            6: RG_Ch_6,
            7: RG_Ch_7
        }.get(ch, RG_Ch_0) # Get ch, default is RG_Ch_0
        return self.readRegister(reg)

    def setChannelRange(self, ch, ch_range):
        reg = {
            0: RG_Ch_0,
            1: RG_Ch_1,
            2: RG_Ch_2,
            3: RG_Ch_3,
            4: RG_Ch_4,
            5: RG_Ch_5,
            6: RG_Ch_6,
            7: RG_Ch_7
        }.get(ch, RG_Ch_0) # Get ch, default is RG_Ch_0
        self.writeRegister(reg, ch_range)

    def setGlobalRange(self, ch_range):
        for i in range(self.nr_channels):
            self.setChannelRange(i, ch_range)
    """     
    #--------------------------------------------------        
    def getId(self):
        return (self.getFeatureSelect() >> 6)

    def setId(self, id):
        self._feature = (self._feature & 0b00010111) | ((id & 0b11)<<6)
        self.writeRegister(FT_SEL, self._feature)

    def getAlarm(self):
        return (self.getFeatureSelect() >> 4) & 1

    def setAlarm(self, alarm):
        self._feature = (self._feature & 0b11000111) | ((alarm == True)<<4)
        self.writeRegister(FT_SEL, self._feature)

    def getSdo(self):
        return (self.getFeatureSelect() & 0b111)

    def setSdo(self, sdo):
        self._feature = (self._feature & 0b11010000) | (sdo & 0b111)
        self.writeRegister(FT_SEL, self._feature)

    def getFeatureSelect(self):
        return self.readRegister(FT_SEL)

    def setFeatureSelect(self, id, alarm, sdo):
        self._feature = ((id & 0b11)<<6) | ((alarm == True)<<4) | (sdo & 0b111)
        self.writeRegister(FT_SEL, self._feature)
        
    #--------------------------------------------------        
    def getAlarmOverview(self):
        return self.readRegister(ALARM_OVERVIEW)

    def getFirstTrippedFlag(self):
        return self.readRegister(ALARM_CH0_TRIPPED_FLAG)

    def getSecondTrippedFlag(self):
        return self.readRegister(ALARM_CH4_TRIPPED_FLAG)

    def getTrippedFlags(self):
        MSB = self.readRegister(ALARM_CH0_TRIPPED_FLAG)
        LSB = self.readRegister(ALARM_CH4_TRIPPED_FLAG)
        return (MSB << 8) | LSB

    def getFirstActiveFlag(self):
        return self.readRegister(ALARM_CH0_ACTIVE_FLAG)

    def getSecondActiveFlag(self):
        return self.readRegister(ALARM_CH4_ACTIVE_FLAG)

    def getActiveFlags(self):
        msb = self.readRegister(ALARM_CH0_ACTIVE_FLAG)
        lsb = self.readRegister(ALARM_CH4_ACTIVE_FLAG)
        return (msb << 8) | lsb

    #--------------------------------------------------
    def getChannelHysteresis(self, ch: int) -> int:
        reg = 5 * (7 if ch > 7 else ch) + CH0_HYST
        return self.readRegister(reg)

    def getChannelLowThreshold(self, ch: int) -> int:
        reg = 5 * (7 if ch > 7 else ch) + CH0_LT_MSB
        MSB = self.readRegister(reg)
        LSB = self.readRegister(reg + 1)
        return (MSB << 8) | LSB

    def getChannelHighThreshold(self, ch: int) -> int:
        reg = 5 * (7 if ch > 7 else ch) + CH0_HT_MSB
        MSB = self.readRegister(reg)
        LSB = self.readRegister(reg + 1)
        return (MSB << 8) | LSB

    def setChannelHysteresis(self, ch: int, val: int) -> None:
        reg = 5 * (7 if ch > 7 else ch) + CH0_HYST
        self.writeRegister(reg, val)

    def setChannelLowThreshold(self, ch: int, val: int) -> None:
        reg = 5 * (7 if ch > 7 else ch) + CH0_LT_MSB
        self.writeRegister(reg, val >> 8)
        self.writeRegister(reg + 1, val & 255)

    def setChannelHighThreshold(self, ch: int, val: int) -> None:
        reg = 5 * (7 if ch > 7 else ch) + CH0_HT_MSB
        self.writeRegister(reg, val >> 8)
        self.writeRegister(reg + 1, val & 255)

    def getCommandReadBack(self) -> int:
        return self.readRegister(self.CMD_READBACK)
    """   
    
    #--------------------------------------------------
    def get_scale(self, ch_range):
        if ch_range == R1:
            _min = -1.25 * self.vref
            _max = 1.25 * self.vref
        elif ch_range == R2:
            _min = -0.625 * self.vref
            _max = 0.625 * self.vref
        elif ch_range == R3:
            _min = -0.3125 * self.vref
            _max = 0.3125 * self.vref
        elif ch_range == R4:
            _min = -0.15625 * self.vref
            _max = 0.15625 * self.vref
        elif ch_range == R5:
            _min = 0 * self.vref
            _max = 2.5 * self.vref
        elif ch_range == R6:
            _min = 0 * self.vref
            _max = 1.25 * self.vref
        elif ch_range == R7:
            _min = 0 * self.vref
            _max = 0.625 * self.vref
        elif ch_range == R8:
            _min = 0 * self.vref
            _max = 0.3125 * self.vref
        else:
            _min = -2.5 * self.vref
            _max = 2.5 * self.vref
            
        return _min, _max
    
    #--------------------------------------------------
    def raw2volt(self, val, ch_range):
        out_min, out_max = self.get_scale(ch_range)
        result = val*(out_max - out_min) / 65535. + out_min
        return result
    
    def volt2raw(self, val, ch_range):
        in_min, in_max = self.get_scale(ch_range)
        result = (val-in_min) * 65535. / (in_max-in_min)
        return result

    #--------------------------------------------------   
    def writeRegister(self, reg, val):
        self.CSON()
        result = self.spi.xfer2([(reg << 1) | 0x01, val, 0x00])[-1]
        self.CSOFF()
        self.mode = MODE_PROG
        return result
        
    def readRegister(self, reg):
        self.CSON()
        result = self.spi.xfer2([(reg << 1) | 0x00, 0x00, 0x00])[-1]
        #self.spi.xfer2([(reg << 1) | 0x00])
        #self.spi.xfer2([0x00])
        #result = self.spi.xfer2([0x00])
        self.CSOFF()
        self.mode = MODE_PROG
        return result
         
    def cmdRegister(self, reg):
        self.CSON()
        self.spi.xfer2([reg, 0x00])
        result = 0
        if (self.mode in [1, 5, 6, 7]):
            # only 16 bit if POWERDOWN or STDBY or RST or IDLE
            #msb = self.spi.xfer2([0x00])[0]
            #lsb = self.spi.xfer2([0x00])[0]
            #result = ( msb << 8) | lsb
            ret = self.spi.xfer2([0x00, 0x00])
            result = ( ret[0] << 8) | ret[1]
        self.CSOFF()
        
        # when exit power down it takes 15 ms to be operational
        if self.mode == MODE_POWER_DN:
            time.sleep(0.015)

        if reg == NO_OP:
            if self.mode == MODE_RESET or self.mode == MODE_PROG:
                self.mode = MODE_IDLE
            elif self.mode == MODE_AUTO_RST:
                self.mode = MODE_AUTO
        elif reg == STDBY:
            self.mode = MODE_STANDBY
        elif reg == PWR_DN:
            self.mode = MODE_POWER_DN
        elif reg == RST:
            self.mode = MODE_RESET
        elif reg == AUTO_RST:
            self.mode = MODE_AUTO_RST
        else:
            self.mode = MODE_MANUAL

        return result

    def CSON(self):
        wp.digitalWrite(self.cs_pin, wp.GPIO.LOW)
        return
    
    def CSOFF(self):
        wp.digitalWrite(self.cs_pin, wp.GPIO.HIGH)
        return