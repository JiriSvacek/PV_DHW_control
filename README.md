# Switching heating of tanks for domestic water according to photovoltaic capacity with Rasberry Pi Pico
## Goal:
Using exces power from photovoltaic power plant to heat water in water heaters. For controling of the whole system is used Rasberry Pi Pico. Code has implemented priorities. If there is high demand from household or there is not enought sunlight to provide power disable individual water heaters in specific order (or turn on in specific order). 
## Compoments:
System has got several compoments. Rasberry Pi pico which is the "brain" and controls three output relays (with LED signalization, in electric switchboard mounted under the Pico). Data for evaluation are colected from baterry - **Seplos BMS** via comunication RS485 and from two electric consumption meter (CM, 2 phases). They are connected on the output side of PV inverters leading to the houshold with water heaters. CM has connectable output that switches according to the current load.
## Rasberry Pi Pico
### Additional modules:
* __Waveshare 2-chanell module RS485__ - Used for communication with battery (or BMS) from Seplos. Protocol offers lot of informations which can be read. In this project there are only three parameters used: **Current [A]**, **Status of charge[%]** and _only for display purposes_ **Voltage[V]**
* __Waveshare RTC DS3231__ - If there is blackout, this module can provide actual time after Pico boots up. The control of water heaters is working only during a day (8 - 18)
* __IPS LCD display 0,96" 160x80px - SPI - 65K RGB__ - Shows battery parameters during the day. In the night there is running countdown for next start. Plus in footer there is shown actual time and date.
### Inputs
* __Pin 0, 1__ - UART, comunication with battery
* __Pin 8, 9, 10, 11, 12__ - LCD display
* __Pin 15__ - Push button on LCD, during off time if is pressed instead of countdown to the next start, battery data are shown
* __Pin 20, 21__ - I2C, RTC synchronization
* __Pin 26__ - Switching output from electric consumption meter at phase 1
* __Pin 27__ - Switching output from electric consumption meter at phase 2

### Outputs
* __Pin 6__ - Water heater with highest priority, connected on phase __1__
* __Pin 7__ - Water heater with normal priority, connected on phase __2__
* __Pin 14__ - Water heater with low priority (big water heater, water is not almost used, backup), connected on phase __1__
  
*__pc_communication.py__ file is additional. It is used to read data directly from Seplos BMS to PC via RS485 converter connected to USB.
![Pico in electric switchboard with stacked modules 1](https://github.com/JiriSvacek/PV_DHW_control/blob/master/pics/pico_stacked_w_modules_1.PNG)
![Pico in electric switchboard with stacked modules 2](https://github.com/JiriSvacek/PV_DHW_control/blob/master/pics/pico_stacked_w_modules_2.PNG)
