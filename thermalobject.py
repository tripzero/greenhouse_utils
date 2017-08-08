"""
	thermal object
"""
import math

def c_to_kelvin(c):
	return c + 273.15

def kelvin_to_c(k):
	return k - 273.15

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

def radiantEnergy(emissivity, surfaceArea, temperature):
	" Q = emissivity * 5.67x10-8 * surfaceArea * (temperature^4 - temperature2^4)"

	return emissivity * (5.67 * math.pow(10, -8)) * surfaceArea * (math.pow(temperature, 4))


class ThermalConstants:
	class Emissivity:
		soil = 0.38
		water = 0.67
		blackBody = 1
		aluminum = 0.09

	class Density:
		"g/m^3"
		air = 1225
		soil = 1600000
		water =  1000000
		aluminum = 2712000


	class SpecificHeat:
		"measured in J/g"
		water = 4.184
		soil = 1.480
		air = 1.003
		aluminum = 0.9

	class Conductivity:
		"in joules/(sec*m*C) or k-value"
		soil = 1.0
		water = 0.58
		pex = 0.4
		air = 0.024
		aluminum = 205
		glass = 0.8



class ThermalObject(object):

	def __init__(self, specificHeat = None, density=None, conductivity=None, emissivity=None, dimensions=None, temperature = 15, mass=None):
		object.__init__(self)

		self.specificHeat = specificHeat
		self.density = density
		self.conductivity = conductivity
		self.emissivity = emissivity
		self.dimensions = dimensions

		if mass:
			self.mass = mass
			if not dimensions:
				self.dimensions = (math.pow(mass / density, 1 / 3.0), math.pow(mass / density, 1 / 3.0), math.pow(mass / density, 1 / 3.0))

		elif dimensions != None:
			self.mass = dimensions[0] * dimensions[1] * dimensions[2] * self.density

		self.temperature = temperature

	@property
	def massR(self):
		"m = c^2/e"
		return self.energy / math.pow(299792458, 2)

	@property
	def energy(self):
		return energyCapacity(self.specificHeat, self.mass, self.temperature)

	@energy.setter
	def energy(self, value):
		self.temperature = temperature(self.specificHeat, self.mass, value)

	def addEnergy(self, value):
		self.energy += value

	def estimateContactArea(self, otherObject=None):

		if not len(self.dimensions):
			return None

		if otherObject:
			#get contact area:
			a1 = max(otherObject.dimensions[0] * otherObject.dimensions[1], otherObject.dimensions[0] * otherObject.dimensions[2])
			a1 = max(a1, otherObject.dimensions[1] * otherObject.dimensions[2])

		a2 = max(self.dimensions[0] * self.dimensions[1], self.dimensions[0] * self.dimensions[2])
		contactArea = a2

		if otherObject:
			a2 = max(a2, otherObject.dimensions[1] * self.dimensions[2])
			contactArea = min(a1, a2)


		return contactArea


	def transferTo(self, otherObject, contactArea=None, time=1, convection=False, length=1):

		if not contactArea:
			contactArea = self.estimateContactArea(otherObject)

		tf = otherObject.temperature
		ts = self.temperature
		conductivity = otherObject.conductivity

		if self.temperature < otherObject.temperature:
			conductivity = self.conductivity
			tf = self.temperature
			ts = otherObject.temperature

		et = None

		if not convection:
			et = energyTransferred(conductivity, tf, ts, contactArea, time, length)

		else:
			et = convectionEnergyTransfer(contactArea, otherObject.temperature, self.temperature)


		totalEt=et

		if conductivity == self.conductivity:
			self.removeEnergy(et)
			otherObject.addEnergy(et)
		else:
			otherObject.removeEnergy(et)
			self.addEnergy(et)

		return totalEt

	def removeEnergy(self, energy):
		self.energy -= energy

	def radiate(self, contactArea = None, seconds = 1):
		if not contactArea:
			contactArea = self.estimateContactArea()

		totalRadiationLoss = 0

		for s in range(seconds):
			radiation = radiantEnergy(self.emissivity, contactArea, self.temperature)
			self.removeEnergy(radiation)
			totalRadiationLoss += radiation

		return totalRadiationLoss


class Water(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, ThermalConstants.SpecificHeat.water, ThermalConstants.Density.water, ThermalConstants.Conductivity.water, ThermalConstants.Emissivity.water, dimensions, temperature, mass=mass)


class Soil(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, ThermalConstants.SpecificHeat.soil, ThermalConstants.Density.soil, ThermalConstants.Conductivity.soil, ThermalConstants.Emissivity.soil, dimensions, temperature, mass=mass)

class Air(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None, humidity=0):
		ThermalObject.__init__(self, ThermalConstants.SpecificHeat.air, ThermalConstants.Density.air, ThermalConstants.Conductivity.air, ThermalConstants.Emissivity.blackBody, dimensions, temperature, mass=mass)
		self.humidity = humidity

	@property
	def dewpoint(self):
		T = self.temperature
		RH = self.humidity

		dp = 243.04 * (math.log(RH / 100.0) + ((17.625 * T) / (243.04 + T))) / (17.625 - math.log(RH / 100.0) - ((17.625 * T) / (243.04 + T)))

		return dp




class Aluminum(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, ThermalConstants.SpecificHeat.aluminum, ThermalConstants.Density.aluminum, ThermalConstants.Conductivity.aluminum, ThermalConstants.Emissivity.aluminum, dimensions, temperature, mass=mass)


class Glass(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, 753, 2600000, 0.8, 0, dimensions=dimensions, temperature=temperature, mass=mass)

