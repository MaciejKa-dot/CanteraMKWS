import numpy as np
import pkg_resources
import cantera as ct
import math
import csv
import matplotlib.pyplot as plt

gas = ct.Solution('gri30.xml')

temp = 1300.0
pressure = 25.0

#parametry zbiornika paliwa
fuel_T = temp #temperatura różna w zależności od przypadku
fuel_P = pressure*ct.one_atm #cisnienie różne w zależności od przypadku 
fuel_X = 'CH4:1.0'
gas.TPX = fuel_T, fuel_P, fuel_X    #metan
fuel = ct.Reservoir(gas)
fuel_mw = gas.mean_molecular_weight
fuel_k = gas.cp/gas.cv

#parametry zbiornika utleniacza
oxidizer_T = temp #temperatura różna w zależności od przypadku
oxidizer_P = pressure*ct.one_atm #cisnienie różne w zależności od przypadku 
oxidizier_X = 'O2:1.0'
gas.TPX = oxidizer_T, oxidizer_P, oxidizier_X    #tlen
oxidizer = ct.Reservoir(gas)
oxidizer_mw = gas.mean_molecular_weight
oxidizer_k = gas.cp/gas.cv

#zrodlo zaplonu - wolne rodniki wodoru
gas.TPX = 300.0, ct.one_atm, 'H:1.0'
igniter = ct.Reservoir(gas)

#komora spalania silnika
gas.TPX = 300.0, 1.1*ct.one_atm, 'O2:1.0'   #komora spalania poczatkowo wypelniona tlenem
combustion_chamber = ct.IdealGasReactor(gas)
combustion_chamber.volume = 0.0005

#dysza wylotowa
gas.TPX = 300.0, 1*ct.one_atm, 'N2:1.0'
exhaust = ct.Reservoir(gas)
exaustP = ct.one_atm


#zdefiniowanie potrzebnych funkcji
def kappa(gas):
    return gas.cp/gas.cv

def critical_flow(gasin, gasinP, gasinT, gasinmw, k, gasoutP, area):
    R = ct.gas_constant/gasinmw
    return (area*gasinP*math.sqrt(k/(R*gasinT))*(2/(k+1))**((k+1)/(2*(k-1))))/(gasinP - gasoutP)

vol1 = ct.Valve(fuel, combustion_chamber)
vol2 = ct.Valve(oxidizer, combustion_chamber)
vol3 = ct.Valve(combustion_chamber, exhaust)

#Konfiguracja zapalnika
fwhm = 0.008
amplitude = 0.01
t0 = 0.05
igniter_mdot = lambda t: amplitude * math.exp(-(t - t0) ** 2 * 4 * math.log(2) / fwhm ** 2)
m3 = ct.MassFlowController(igniter, combustion_chamber, mdot=igniter_mdot)

states = ct.SolutionArray(gas, extra=['t', 'mass', 'vol'])

#Symulacja zawiera tylko jeden reaktor
sim = ct.ReactorNet([combustion_chamber])
time = 0.0
tfinal = 0.1

t_step=0.0000025

#Petla obliczeniowa
while time < tfinal:

    vol1.set_valve_coeff(critical_flow(fuel, fuel_P, fuel_T, fuel_mw, fuel_k, gas.P, 4e-5))
    vol2.set_valve_coeff(critical_flow(oxidizer, oxidizer_P, oxidizer_T, oxidizer_mw, oxidizer_k, gas.P, 4e-5))
    vol3.set_valve_coeff(critical_flow(gas, gas.P, gas.T, gas.mean_molecular_weight, kappa(gas), exaustP, 1e-3))

    sim.advance(time)
    time += t_step

    vol = (2 * (kappa(gas) * ct.gas_constant / gas.mean_molecular_weight) / (kappa(gas) - 1) * gas.T * (
    1 - (exaustP / gas.P)) ** ((kappa(gas) - 1) / kappa(gas))) ** 0.5
    states.append(gas.state, t=time, mass=combustion_chamber.mass, vol=vol)
    print(round(time, 5), round(gas.P / 1e6, 3), round(gas.T - 273, 3), round(combustion_chamber.mass*1000, 3), vol)

#Wykres temperatury w czasie
fig = plt.figure()
ax1 = fig.add_subplot(111)
plt.xlabel('$t[s]$')
ax1.plot(states.t, states.T, 'g-')
ax1.set_ylabel('$T [K]$', color='green')
for tl in ax1.get_yticklabels():
    tl.set_color('green')

#Wykres cisnienia w czasie
ax2 = ax1.twinx()
ax2.plot(states.t, states.P/1e6, 'b-')
ax2.set_ylabel('$P [MPa]$', color='blue')
for tl in ax2.get_yticklabels():
    tl.set_color('b')
plt.savefig('T_p_plot.pdf')
plt.show()

#Wykres predkosci wylotowej, zmieniajacej sie w czasie
plt.figure()
plt.grid(ls='dotted')
plt.xlabel('$t[s]$')
plt.ylabel('$V [m/s]$')
plt.plot(states.t, states.v)
plt.savefig('v_plot.pdf')
plt.show()

#Wykres skladu czasteczkowego mieszaniny w zaleznosci od czasu
plt.figure()
plt.grid(ls='dotted')
plt.xlabel('$t[s]$')
plt.ylabel('$[-]$')
plt.plot(states.t, states('CH4').Y, label='CH4')
plt.plot(states.t, states('O2').Y, label='O2')
plt.plot(states.t, states('H2O').Y, label='H2O')
plt.plot(states.t, states('CO2').Y, label='CO2')
plt.plot(states.t, states('CO').Y, label='CO')
plt.legend(loc='upper right')
plt.savefig('concentration_plot.pdf')
plt.show()# -*- coding: utf-8 -*-
"""

"""

