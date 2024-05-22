# Switching heating of tanks for domestic water according to photovoltaic capacity with Rasberry Pi Pico
## Goal:
Using exces power from photovoltaic power plant to heat water in water heaters. For controling of the whole system is used Rasberry Pi Pico. Code has implemented priorities. If there is high demand from household or there is not enought sunlight to provide power disable individual water heaters in specific order (or turn on in specific order). 
## Compoments:
System has got several compoments. Rasberry Pi pico which is the "brain" and controls three output relays (with LED signalization, in electric switchboard mounted under the Pico). Data for evaluation are colected from baterry - **Seplos BMS** via comunication RS485 and from two electric consumption meter (CM, 2 phases). They are connected on the output side of PV inverters leading to the houshold with water heaters. CM has connectable output that switches according to the current load.
## Rasberry Pi Pico
### Additional modules:
* __Waveshare 2-chanell module RS485__ - Used for communication with battery (or BMS) from Seplos. Protocol offers lot of informations which can be read. In this project there are only several parameters used: **Current [A]**, **Status of charge[%]** and _only for display purposes_ **Voltage[V]** and **Cycles** 
* __Waveshare RTC DS3231__ - If there is blackout, this module can provide actual time after Pico boots up. Now it is used only for showing correct time.
* __IPS LCD display 1,14" 240x160px - SPI - 65K RGB__ - Shows nessesary parameters voltage, current, SOC and cycles of battery and if heaters are enabled and if power plant disconected from grid.
### Inputs
* __Pin 0, 1__ - UART, comunication with battery
* __Pin 8, 9, 10, 11, 12__ - LCD display
* __Pin 20, 21__ - I2C, RTC synchronization
* __Pin 26__ - Switching output from electric consumption meter at phase 1
* __Pin 27__ - Switching output from electric consumption meter at phase 2

### Outputs
* __Pin 6__ - Water heater with highest priority, connected on phase __1__
* __Pin 7__ - Water heater with normal priority, connected on phase __2__
* __Pin 14__ - Water heater with low priority, connected on phase __1__
* __Pin 22__ - Disconnect from grid.

### Version update from 2022
22.5.2024 - There was update of old code. Mainly refactoring and simplifying code and logic. Added support for disconecting from grid if there is enough battery capacity (SOC). Logging of cycles to additional file. Loading and saving variables to config file.
  
*__pc_communication.py__ file is additional. It is used to read data directly from Seplos BMS to PC via RS485 converter connected to USB.
![Pico with display](https://github.com/JiriSvacek/PV_DHW_control/blob/master/pics/display.PNG)
