#!/usr/bin/env python

from ast import And
from collections import OrderedDict
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.compat import IS_PYTHON3, PYTHON_VERSION
import json
import FroniusModbusLib as FLib

if IS_PYTHON3 and PYTHON_VERSION >= (3, 4):
    import asyncio
    import logging
    # ----------------------------------------------------------------------- #
    # Import the required asynchronous client
    # ----------------------------------------------------------------------- #
    from pymodbus.client.asynchronous.tcp import AsyncModbusTCPClient as ModbusClient
    # from pymodbus.client.asynchronous.udp import (
    #     AsyncModbusUDPClient as ModbusClient)
    from pymodbus.client.asynchronous import schedulers

else:
    import sys
    sys.stderr("This example needs to be run only on python 3.4 and above")
    sys.exit(1)

from threading import Thread
import time


logging.basicConfig()
log = logging.getLogger()
#log.setLevel(logging.DEBUG)


UNIT = 0x01
HOST_Inverter = "192.168.2.215"
PORT_Inverter = 502

def validator(registers, type, expectedSize):        
    wynik = ""    
    decoder = BinaryPayloadDecoder.fromRegisters(registers, Endian.Big, wordorder=Endian.Little)
    
    if type == "int16":
        try:                
            wynik = (decoder.decode_16bit_int())
        except: 
            pass 
    elif type == "uint16":
        try:                
            wynik = (decoder.decode_16bit_uint())
        except: 
            pass 
    elif type == "String16" or type == "String32":            
        try:   
            decoder = BinaryPayloadDecoder.fromRegisters(registers, Endian.Little, wordorder=Endian.Big)             
            wynik = decoder.decode_string(expectedSize)
            wynik = wynik.decode('UTF-8')
            wynik = wynik.rstrip('\x00')
        except: 
            pass         
    elif type == "uint16":
        try:                
            wynik = (decoder.decode_16bit_uint())
        except: 
            pass 
    elif type == "uint32":
        try:                
            wynik = (decoder.decode_32bit_uint())
        except: 
            pass 

    return wynik
    

def splitReg(startAdress, registers, start, size):
    startOffset = (int(start) - int(startAdress))
    h = []
    for x in range(0,size):
        offset =int(startOffset)+int(x)
        h.append(registers[offset])
    return h

async def get_values_async(client):

    #d0 = (40001,68);
    #d1 = (40072,125);
    #d2 = ((ushort)(40072 + 125), 115);

    # string 1
    #40283	1_DCA	DC Current
    #40284	1_DCV	DC Voltage
    #40285  1_DCW	DC Power

    # string 2
    #40303  2_DCA	DC Current
    #40304  2_DCV	DC Voltage
    #40305  2_DCW	DC Power

    #rodzaj = FLib.Rozkazy[str(40005)].type
    #expectedSize = FLib.Rozkazy[str(40005)].size
    #req1 = await Download(client,40001, 68)
    #await asyncio.sleep(1)
    #req2 = await Download(client,40072, 125)
    #await asyncio.sleep(1)
    dict = await Download(client,40197, 119)
    #dict = req1 | req2 | req3        
    
    dictionary = {'body': 
                    { 
                        'data':{ 
                            'dc_current1' : { 
                                'Unit' : str(FLib.Rozkazy['40283'].tekst1), 
                                'Value' :str(float(dict['40283']) / 10)  
                            },
                            'dc_voltage1' : { 
                                'Unit' : str(FLib.Rozkazy['40284'].tekst1), 
                                'Value' :str(float(dict['40284']) / 10)  
                            },
                            'dc_power1' : { 
                                'Unit' : str(FLib.Rozkazy['40285'].tekst1), 
                                'Value' :str(float(dict['40285']) / 100)  
                            },


                            'dc_current2' : { 
                                'Unit' : str(FLib.Rozkazy['40303'].tekst1), 
                                'Value' :str(float(dict['40303']) / 10)  
                            },
                            'dc_voltage2' : { 
                                'Unit' : str(FLib.Rozkazy['40304'].tekst1), 
                                'Value' :str(float(dict['40304']) / 10)  
                            },
                            'dc_power2' : { 
                                'Unit' : str(FLib.Rozkazy['40305'].tekst1), 
                                'Value' :str(float(dict['40305']) / 100)  
                            },
                        } 
                    } 
                }
    
    
    jsonString = json.dumps(dictionary, indent=4)
    return jsonString
    

async def  Download(client, adres = 40072,  dlugosc = 125):

    AdressBezOffset = adres
    adres = adres - 1
    maksDlugosc = adres + dlugosc    
    
    ostatni =  int(list(FLib.Rozkazy)[-1])
    maxIndeks = ostatni  +int(FLib.Rozkazy[str(ostatni)].size)
        
    if (adres + dlugosc) > maxIndeks:    
        dlugosc = (maxIndeks - adres)
    
    if not client:
        raise ConnectionError("Modbus Device is not avaiable")
    
    data = await client.read_holding_registers(adres, dlugosc, unit=UNIT)
    przetworzone = {}

    for r in FLib.Rozkazy:                      
        strr = str(r)        
        if int(r) >= AdressBezOffset and int(r) <= maksDlugosc:
            
            startReg = FLib.Rozkazy[strr].start
            sizeReg = FLib.Rozkazy[strr].size
            try:                            
                if not data.isError():
                    temp = splitReg(AdressBezOffset, data.registers, startReg ,sizeReg)

                    zmienna = str(validator(temp, FLib.Rozkazy[strr].type, FLib.Rozkazy[strr].size))
                    lv = str(FLib.Rozkazy[strr].tekst1.lower)                                                
                    if lv!= "bitfield" and lv != "cos()":                
                        #zmienna += " "+ str(FLib.Rozkazy[strr].tekst1)                    
                        przetworzone[str(FLib.Rozkazy[strr].start)] = zmienna
            except Exception as e:    
                if hasattr(e, 'message'):
                    print(e.message)
                else:
                    print(e)
                
    return przetworzone




def pobierzWartosci():
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop, client = ModbusClient(schedulers.ASYNC_IO, host=HOST_Inverter, port=PORT_Inverter)
    result = loop.run_until_complete(get_values_async(client.protocol))
    loop.close()
    return result

if __name__ == '__main__':
   test = pobierzWartosci()
   print(test)
    
    
    
