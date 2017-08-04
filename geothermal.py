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
from datetime import datetime, timedelta
from thermalobject import *

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
		result = f.read().decode('utf-8')

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

def findSoilBankArea(waterMass, waterSurfaceArea, soilBedMass, soilBedSurfaceArea, minimumTemperature, greenhouseDimensions, startingTemperature = 15, year=2015, debug=False):
	import pdb
	from pysolar import radiation
	from pysolar import solar

	greenhouseVolume = greenhouseDimensions[0] * greenhouseDimensions[1] * greenhouseDimensions[2]
	greenhouseHeight = greenhouseDimensions[2]
	greenhouseSurfaceArea = greenhouseDimensions[0] * greenhouseDimensions[1]

	airMass = greenhouseVolume * ThermalConstants.Density.air
	soilBankMass = 10 #g
	soilBedVolume = soilBedMass / ThermalConstants.Density.soil

	pexRadius = 1.5875 #cm
	surfaceAreaPex = (2 * math.pi * pexRadius) / 100 #m^2

	solar_efficiency = 0.7
	greenhouse_effect = 0.10 #you will regain this percentage of radiated energy

	fail = True
	failDate = None
	failTemperature = None

	while fail:
		water = Water(mass = waterMass, temperature = startingTemperature)
		soilBank = Soil(mass = soilBankMass, temperature = startingTemperature)
		soilBed = Soil(mass = soilBedMass, temperature = startingTemperature)
		greenhouse = Soil(mass = greenhouseSurfaceArea * ThermalConstants.Density.soil, temperature = startingTemperature)
		air = Air(mass = airMass, temperature = startingTemperature)
		air_outside = Air(mass = 99999999999999, temperature = startingTemperature)

		soilBankVolume = soilBankMass / ThermalConstants.Density.soil

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

			print("calculating day: {}.  Soil bed: {}, water: {}, greenhouse: {}".format(date, soilBed.temperature, water.temperature, greenhouse.temperature))

			air_high_temp = 15

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

				air_outside.temperature = outsideAirTemp

				"add solar energy to system:"

				water.energy += solarPower * waterSurfaceArea * solar_efficiency
				greenhouse.energy += solarPower * greenhouseSurfaceArea * solar_efficiency

				"the soil bed is likely shadowed by plants"
				#soilBed.energy += solarPower * soilBedSurfaceArea * solar_efficiency

				"transfer energy first to soil bed then remove the energy transferred from the water"
				pl = pexLength(surfaceAreaPex, soilBedVolume)

				water.transferTo(soilBed, pl, length=0.22)

				"now transfer energy to the soil bank from water:"

				pl = pexLength(surfaceAreaPex, soilBankVolume)

				water.transferTo(soilBank, pl, length=0.22)

				"radiant aisle heating"
				pl = pexLength(surfaceAreaPex, greenhouseSurfaceArea * 0.06)

				water.transferTo(greenhouse, pl)

				"greenhouse surface area can xfer to soilBed too"

				greenhouse.transferTo(soilBed, soilBedSurfaceArea)

				"caculate losses to the air."

				greenhouse.transferTo(air, greenhouseSurfaceArea)
				soilBed.transferTo(air, soilBedSurfaceArea)
				water.transferTo(air, waterSurfaceArea)

				"determine air loss to outside air"

				airInsulationThickness = 0.127 #m

				air.transferTo(air_outside, greenhouseSurfaceArea, length = airInsulationThickness)

				"radiate to the outside world minus greenhouse effect"

				greenhouse.energy += greenhouse.radiate() * greenhouse_effect
				water.energy += water.radiate() * greenhouse_effect
				soilBed.energy += soilBed.radiate() * greenhouse_effect
				#air.radiate()

				if air.temperature > air_high_temp:
					air_high_temp = air.temperature

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

			print("daily high air temp: {}".format(air_high_temp))

			"check to see if we are colder than the min temperature"
			if soilBed.temperature < minimumTemperature:
				failDate = date
				failTemperature = soilBed.temperature
				fail = True
				if hasOtherSide:
					pyotherside.send("failDate", failDate)

				print("We failed at {0} with soil bed temperature = {1}C and soil bank mass = {2}g".format(failDate, failTemperature, soilBankMass))
				print("air temps: inside: {}C outside: {}C".format(air.temperature, air_outside.temperature))

		if fail:
			"we kinda failed, so let's double our soilBankVolume and try again"
			soilBankMass += soilBankMass

	print ("success with soil bank mass: {0}".format(soilBankMass))

if __name__ == "__main__":

	waterMass = 0.20819755 * ThermalConstants.Density.water #m^3 * density (g/m^3).  55 gallons = 0.2082 cu meters
	waterSurfaceArea = 0.74322432 #m^2.  This is 2ft by 4ft square (0.6096 * 1.2192)
	soilBedMass = 424753 #g
	soilBedDimensions = (3.6576, 0.4572, 0.3048) #m
	soilBedSurfaceArea = soilBedDimensions[0] * soilBedDimensions[1] #m^2
	minimumTemperature = 0
	startingTemperature = 15
	greenhouseDimensions = (4.8768, 1.8288, 2.7432) #g; density of air is 1225g/m^3.  We could also factor in humidity to add density but maybe later
	debug = False

	findSoilBankArea(waterMass, waterSurfaceArea, soilBedMass, soilBedSurfaceArea,  minimumTemperature, greenhouseDimensions, startingTemperature = startingTemperature, debug = debug)
