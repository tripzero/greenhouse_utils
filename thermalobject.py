"""
	thermal object
"""

import geothermal

class ThermalObject(object):
	specificHeat = None
	density = None
	conductivity = None
	emissivity = None

	temperature = 15

	def __init__(self, specificHeat = None, density=None, conducitivty=None, emissivity=None, dimensions=None, temperature = 15, mass=None):
		object.__init__(self)

		self.specificHeat = specificHeat
		self.density = density
		self.conducitivty = conducitivty
		self.emissivity = emissivity
		if mass:
			self.mass = mass
		elif dimensions != None:
			self.mass = dimensions[0] * dimensions[1] * dimensions[2] * self.density
		self.dimensions = dimensions
		self.temperature = temperature


	@property
	def energy(self):
		return geothermal.energyCapacity(self.specificHeat, self.mass, self.temperature)

	def estimateContactArea(self, otherObject=None):
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

		totalEt=0

		for s in range(time):
			conducitivty = otherObject.conducitivty

			tf = otherObject.temperature
			ts = self.temperature

			if self.temperature > otherObject.temperature:
				conducitivty = self.conducitivty
				tf = self.temperature
				ts = otherObject.temperature

			et = None

			if not convection:
				et = geothermal.energyTransferred(conducitivty, tf, ts, contactArea, 1, length)

			else:
				et = geothermal.convectionEnergyTransfer(contactArea, otherObject.temperature, self.temperature)


			totalEt+=et

			self.removeEnergy(et)
			otherObject.addEnergy(et)

		return totalEt

	def addEnergy(self, energy):
		self.temperature = geothermal.temperature(self.specificHeat, self.mass, energy + self.energy)

	def removeEnergy(self, energy):
		self.addEnergy( -1 * energy)

	def radiate(self, contactArea = None, time = 1):
		if not contactArea:
			contactArea = self.estimateContactArea()

		totalRadiationLoss = 0

		for s in range(time):
			print (self.emissivity, contactArea, self.temperature)

			radiation = geothermal.radiantEnergy(self.emissivity, contactArea, self.temperature)
			self.removeEnergy(radiation)
			totalRadiationLoss += radiation

		return totalRadiationLoss


class Water(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, geothermal.ThermalConstants.SpecificHeat.water, geothermal.ThermalConstants.Density.water, geothermal.ThermalConstants.Conductivity.water, geothermal.ThermalConstants.Emissivity.water, dimensions, temperature, mass=mass)


class Soil(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, geothermal.ThermalConstants.SpecificHeat.soil, geothermal.ThermalConstants.Density.soil, geothermal.ThermalConstants.Conductivity.soil, geothermal.ThermalConstants.Emissivity.soil, dimensions, temperature, mass=mass)

class Air(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, geothermal.ThermalConstants.SpecificHeat.air, geothermal.ThermalConstants.Density.air, geothermal.ThermalConstants.Conductivity.air, geothermal.ThermalConstants.Emissivity.blackBody, dimensions, temperature, mass=mass)


class Aluminum(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, geothermal.ThermalConstants.SpecificHeat.aluminum, geothermal.ThermalConstants.Density.aluminum, geothermal.ThermalConstants.Conductivity.aluminum, geothermal.ThermalConstants.Emissivity.aluminum, dimensions, temperature, mass=mass)


class Glass(ThermalObject):

	def __init__(self, dimensions=None, temperature=15, mass=None):
		ThermalObject.__init__(self, 753, 2600000, 0.8, 0, dimensions=dimensions, temperature=temperature, mass=mass)

