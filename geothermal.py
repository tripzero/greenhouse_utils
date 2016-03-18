#!/usr/bin/env python3

'''
Equations:
Heat conductivity:

Q = (kA(T2-T1)t)/D

TempFinal = (M1* C1 * T1 + M2 * C2 * T2) / (M1 * C1 + M2 * C2)

Q = mC  (T2-T1)

Q = (planksConstant * speedOfLight) / wavelength

wavelength = 0.0029 / temperature

TempFinal = Q / mc
'''

from astral import Location
from pysolar import radiation
from pysolar import solar
from datetime import datetime, timedelta
import math
import time as tm
import os.path

import json
from urllib.request import urlopen

import pdb

import sys
sys.setrecursionlimit(10000)

hasOtherSide = False

try:
	import pyotherside
	print("running in pyotherside")
	hasOtherSide = True
except:

	hasOtherSide = False

def debugOut(msg):
	if hasOtherSide:
		pyotherside.send("debug", msg)
	else:
		print(msg)


def tempFinal(mass1, specificHeat1, temp1, mass2, specificHeat2, temp2):
	return (mass1 * specificHeat1 * temp1 + mass2 * specificHeat2 * temp2) / (mass1 * specificHeat1 + mass2 * specificHeat2)

def energyTransferred(k, tempFinal, tempStart, area, time, distance):
	"this is for conduction"
	return (k * area * (tempFinal - tempStart) * time) / distance

def convectionEnergyTransfer(area, tempFinal, tempStart):

	deltaT = (tempFinal - tempStart)
	q = 1.77 * area * math.pow(abs(deltaT), 5.0/4.0)

	if deltaT < 0:
		q *= -1

	return q

def energyCapacity(c, m, t):
	return m * c * t

def time(k, area, tempHot, tempStart, distance, energy):
	return (k * area * (tempHot - tempCold)) / (distance * energy)

def temperature(c, mass, energy):
	return energy / (c * mass)

def radiantEnergy(emissivity, surfaceArea, temperature, temperature2 = -273):
	" Q = emissivity * 5.67x10-8 * surfaceArea * (temperature^4 - temperature2^4)"
	"We assume temp is C, we want K here"

	temperature = 273 + temperature
	temperature2 = 273 + temperature2

	return emissivity * (5.67 * math.pow(10, -8)) * surfaceArea * (math.pow(temperature, 4) - math.pow(temperature2, 4))

def wuGetAirTemperature(date):

	"first try to see if we have a cached file for this day:"
	filename = "weather/weather_{0}.json".format(date.strftime("%Y%m%d"))
	result = ""

	if os.path.isfile(filename):
		with open(filename, "r") as f:
			result = f.read()
	else:
		'''http://api.wunderground.com/api/Your_Key/history_YYYYMMDD/q/OR/Hillsboro.json'''
		f = urlopen('http://api.wunderground.com/api/cbd714e056969068/history_{0}/q/OR/Hillsboro.json'.format(date.strftime("%Y%m%d")))
		result = f.readall().decode('utf-8')

		with open(filename, "w") as f:
			f.write(result)

	w = json.loads(result)

	dailySummary = w["history"]["dailysummary"][0]
	meantemp = dailySummary['meantempm']
	maxtemp = dailySummary['maxtempm']
	mintemp = dailySummary['mintempm']
	observations = w["history"]["observations"]

	return mintemp, maxtemp, observations

def weatherGetConditions(date, observations):
	for observation in observations:
		h = observation["date"]["hour"]
		m = dh = observation["date"]["min"]

		if date.hour == int(h) and date.minute == int(m):
			return observation["conds"]

	return None

def getRadiationVisibilityCoefficient(condition):
	if condition == "Fog":
		return 0.1
	elif condition == "Scattered Clouds":
		return 0.5
	elif condition == "Mostly Cloudy":
		return 0.3
	elif condition == "Overcast":
		return 0.2

	return 1.0


class ThermalConstants:
	class Emissivity:
		soil = 0.38
		water = 0.67
		blackBody = 1
		aluminum = 0.09

	class Density: #g/m^3
		air = 1225
		soil = 1600000
		water =  1000000
		aluminum = 2712000


	class SpecificHeat:
		"measured in J/g"
		water = 4184.0
		soil = 1480.0
		air = 1003.0
		aluminum = 900.0

	class Conductivity:
		soil = 1.0
		water = 0.58
		pex = 0.4
		air = 0.024
		aluminum = 205


def calculateGreenhouseEffect(energyIn, soilTemp, airTemp, outsideAirTemp, greenhouseDimensions, surfaceAbsorbtionRate=0.80, glassReflectionRate=0.90):

	surfaceArea = greenhouseDimensions[0] * greenhouseDimensions[1]

	soilMass = greenhouseDimensions[0] * greenhouseDimensions[1] * 0.22 * ThermalConstants.Density.soil # grams
	airMass = greenhouseDimensions[0] * greenhouseDimensions[1] * greenhouseDimensions[2] * ThermalConstants.Density.air

	soilEnergy = energyCapacity(ThermalConstants.SpecificHeat.soil, soilMass, soilTemp)
	airEnergy = energyCapacity(ThermalConstants.SpecificHeat.air, airMass, airTemp)

	soilEnergy += energyIn * surfaceAbsorbtionRate
	airEnergy += energyIn - (energyIn * surfaceAbsorbtionRate)


	thermalConductivity = None

	if soilTemp > airTemp:
		gain = convectionEnergyTransfer(surfaceArea, airTemp, soilTemp)
		soilEnergy -= gain
		airEnergy += gain
	else:
		tf = tempFinal(soilMass, ThermalConstants.SpecificHeat.soil, soilTemp, airMass, ThermalConstants.SpecificHeat.air, airTemp)
		gain = energyTransferred(ThermalConstants.Conductivity.soil, tf, soilTemp, surfaceArea, 1, greenhouseDimensions[2])
		soilEnergy += gain
		airEnergy -= gain

	energyLoss = radiantEnergy(ThermalConstants.Emissivity.soil, surfaceArea, soilTemp, outsideAirTemp)

	soilEnergy -= energyLoss

	#debugOut("SoilEnergy: {0}".format(soilEnergy))

	airTemp = temperature(ThermalConstants.SpecificHeat.air, airMass, airEnergy)
	soilTemp = temperature(ThermalConstants.SpecificHeat.soil, soilMass, soilEnergy)

	return soilTemp, airTemp


def pexLength(pexSurfaceArea, soilBankVolume):
	spacing = 0.11 #m
	return soilBankVolume / pexSurfaceArea * (spacing * 2)

def findSoilBankArea(waterVolume, waterSurfaceArea, soilBedVolume, soilBedSurfaceArea, minimumTemperature, greenhouseDimensions, year=2014, debug=False):
	import pdb

	greenhouseVolume = greenhouseDimensions[0] * greenhouseDimensions[1] * greenhouseDimensions[2] * ThermalConstants.Density.air
	greenhouseHeight = greenhouseDimensions[2]
	greenhouseSurfaceArea = greenhouseDimensions[0] * greenhouseDimensions[1]

	airVolume = greenhouseVolume * ThermalConstants.Density.air
	soilBankVolume = 10 #g
	pexRadius = 1.5875 #cm
	surfaceAreaPex = (2 * math.pi * pexRadius) / 100 #m^2

	fail = True
	failDate = None
	failTemperature = None

	while fail:
		energyWater = energyCapacity(ThermalConstants.SpecificHeat.water, waterVolume, minimumTemperature)
		energySoilBank = energyCapacity(ThermalConstants.SpecificHeat.soil, soilBankVolume, minimumTemperature)
		energySoilBed = energyCapacity(ThermalConstants.SpecificHeat.soil, soilBedVolume, minimumTemperature)
		energyAir = energyCapacity(ThermalConstants.SpecificHeat.air, airVolume, minimumTemperature)
		soilTemp = minimumTemperature

		fail = False
		date = datetime(year, 1, 1)

		for day in range(364):
			if hasOtherSide:
				pyotherside.send("day", day+1)

			if fail:
				break

			minAirTemp, maxAirTemp, observations = wuGetAirTemperature(date)
			condition = "Clear"
			outsideAirTemp = float(minAirTemp)

			"run through every second in the day"
			for second in range(86400):

				solarAlt = solar.get_altitude(45.542384, -122.961576, date)

				solarPower = 0

				cond = weatherGetConditions(date, observations)

				if cond:
					condition = cond

				if solarAlt > 0:
					solarPower = radiation.get_radiation_direct(date, solarAlt)
					"factor in clouds "
					solarPower = solarPower * getRadiationVisibilityCoefficient(condition)
					if solarPower >= 1:
						outsideAirTemp = float(maxAirTemp)
						#debugOut("solarInput: {0}".format(solarPower * greenhouseSurfaceArea))

					else:
						outsideAirTemp = float(minAirTemp)

				airTemp = temperature(ThermalConstants.SpecificHeat.air, airVolume, energyAir)

				"calculate estimated greenhouse effect:"

				soilTemp, airTemp = calculateGreenhouseEffect(solarPower * greenhouseSurfaceArea, soilTemp, airTemp, outsideAirTemp, greenhouseDimensions)

				energyAir = energyCapacity(ThermalConstants.SpecificHeat.air, airVolume, airTemp)

				"add the energy to water with a 0.7 effeciency rate:"
				energyWater += solarPower * waterSurfaceArea * 0.7

				waterTemp = temperature(ThermalConstants.SpecificHeat.water, waterVolume, energyWater)
				soilBedTemp = temperature(ThermalConstants.SpecificHeat.soil, soilBedVolume, energySoilBed)
				soilBankTemp = temperature(ThermalConstants.SpecificHeat.soil, soilBankVolume, energySoilBank)

				"transfer energy first to soil bed then remove the energy transferred from the water"
				tf = tempFinal(waterVolume, ThermalConstants.SpecificHeat.water, waterTemp, soilBedVolume, ThermalConstants.SpecificHeat.soil, soilBedTemp)

				pl = pexLength(surfaceAreaPex, soilBedVolume)

				thermalConductivity = None

				"determine the direction of the heat transfer"

				if tf > soilBedTemp:
					thermalConductivity = ThermalConstants.Conductivity.soil
				else:
					thermalConductivity = ThermalConstants.Conductivity.water

				energySoilBed += energyTransferred(thermalConductivity, tf, soilBedTemp, pl, 1, 0.22)
				energyWater += energyTransferred(thermalConductivity, tf, waterTemp, pl, 1, pexRadius / 100)

				"now transfer energy to the soil bank from water:"

				waterTemp = temperature(ThermalConstants.SpecificHeat.water, waterVolume, energyWater)
				tf = tempFinal(waterVolume, ThermalConstants.SpecificHeat.water, waterTemp, soilBankVolume, ThermalConstants.SpecificHeat.soil, soilBankTemp)

				pl = pexLength(surfaceAreaPex, soilBankVolume)

				thermalConductivity = None

				"determine the direction of the heat transfer"

				if tf > soilBankTemp:
					thermalConductivity = ThermalConstants.Conductivity.soil
				else:
					thermalConductivity = ThermalConstants.Conductivity.water

				energySoilBank += energyTransferred(thermalConductivity, tf, soilBankTemp, pl, 1, 0.22)
				energyWater += energyTransferred(thermalConductivity, tf, waterTemp, pl, 1, pexRadius / 100)

				"caculate losses to the air."

				soilBedTemp = temperature(ThermalConstants.SpecificHeat.soil, soilBedVolume, energySoilBed)

				gain = convectionEnergyTransfer(soilBedSurfaceArea, airTemp, soilBedTemp)

				energySoilBed += gain
				energyAir -= gain

				gain = convectionEnergyTransfer(waterSurfaceArea, airTemp, waterTemp)

				energyWater += gain
				energyAir -= gain

				"Check to see if our soil bed temp is below the setpoint:"

				soilBedTemp = temperature(ThermalConstants.SpecificHeat.soil, soilBedVolume, energySoilBed)
				waterTemp = temperature(ThermalConstants.SpecificHeat.water, waterVolume, energyWater)

				"determine air loss to outside air"

				airInsulationThickness = 0.127 #m

				energyAir += energyTransferred(ThermalConstants.Conductivity.air, outsideAirTemp, airTemp, greenhouseSurfaceArea + (greenhouseHeight * 2), 1, airInsulationThickness)

				airTemp = temperature(ThermalConstants.SpecificHeat.air, airVolume, energyAir)

				if debug:
					pdb.set_trace()

				"emit updated results to UI"
				if hasOtherSide:
					pyotherside.send("waterTemperature", waterTemp)
					pyotherside.send("soilBedTemp", soilBedTemp)
					pyotherside.send("soilBankTemp", soilBankTemp)
					pyotherside.send("date", str(date))
					pyotherside.send("soilBankVolume", soilBankVolume)
					pyotherside.send("airTemp", airTemp)
					pyotherside.send("condition", condition)

				"Check to see if bank temp is higher than soilBed or water.  If so, we need to transfer energy from the bank to the soil"

				date += timedelta(seconds = 1)

			if soilBedTemp < minimumTemperature:
				failDate = date
				failTemperature = airTemp
				fail = True
				if hasOtherSide:
					pyotherside.send("failDate", failDate)
				print("We failed at {0} with temperature = {1} and soil bank mass = {2}".format(failDate, failTemperature, soilBankVolume))
				break

		if fail:
			"we kinda failed, so let's double our soilBankVolume and try again"
			soilBankVolume += soilBankVolume

	print ("success with soil bank mass: {0}".format(soilBankVolume))


waterVolume = 75708.236 #g
waterSurfaceArea = 0.37161216 #m^2.  This is 2ft by 2ft square
soilBedVolume = 424753 #g
soilBedSurfaceArea = 167.15232 #m^2
minimumTemperature = 15
greenhouseDimensions = (4.8768, 1.8288, 2.7432) #g; density of air is 1225g/m^3.  We could also factor in humidity to add density but maybe later


def start(debug=False):
	findSoilBankArea(waterVolume, waterSurfaceArea, soilBedVolume, soilBedSurfaceArea,  15, greenhouseDimensions, debug=debug)

