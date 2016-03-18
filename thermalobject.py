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

	def __init__(self, specificHeat = None, density=None, conducitivty=None, emissivity=None, dimensions=(0,0,0), temperature = 15):
		object.__init__(self)

		self.specificHeat = specificHeat
		self.density = density
		self.conducitivty = conducitivty
		self.emissivity = emissivity
		self.mass = dimensions[0] * dimensions[1] * dimensions[2] * self.density
		self.dimensions = dimensions
		self.temperature = temperature


	@property
	def energy(self):
		return geothermal.energyCapacity(self.specificHeat, self.mass, self.temperature)

	def transferTo(self, otherObject, contactArea=None, time=1, convection=False):

		if not contactArea:
			#get contact area:
			a1 = max(otherObject.dimensions[0] * otherObject.dimensions[1], otherObject.dimensions[0] * otherObject.dimensions[2])
			a1 = max(a1, otherObject.dimensions[1] * otherObject.dimensions[2])

			a2 = max(self.dimensions[0] * self.dimensions[1], self.dimensions[0] * self.dimensions[2])
			a2 = max(a2, otherObject.dimensions[1] * self.dimensions[2])

			contactArea = min(a1, a2)

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
				et = geothermal.energyTransferred(conducitivty, tf, ts, contactArea, 1, 1)

			else:
				et = geothermal.convectionEnergyTransfer(contactArea, otherObject.temperature, self.temperature)

			self.removeEnergy(et)
			otherObject.addEnergy(et)

	def addEnergy(self, energy):
		self.temperature = geothermal.temperature(self.specificHeat, self.mass, energy + self.energy)

	def removeEnergy(self, energy):
		self.addEnergy( -1 * energy)

	def radiate(self, contactArea = None, time = 1):

		if contactArea.__class__ == list:
			area = 1
			for d in contactArea:
				area *= self.dimensions[d]
			contactArea = area

		totalRadiationLoss = 0

		for s in range(time):
			radaition += geothermal.radiantEnergy(self.emissivity, contactArea, self.temperature)
			self.removeEnergy(radiation)
			totalRadiationLoss += radiation

		return totalRadiationLoss


class Water(ThermalObject):

	def __init__(self, dimensions, temperature=15):
		ThermalObject.__init__(self, geothermal.ThermalConstants.SpecificHeat.water, geothermal.ThermalConstants.Density.water, geothermal.ThermalConstants.Conductivity.water, geothermal.ThermalConstants.Emissivity.water, dimensions, temperature)


class Soil(ThermalObject):

	def __init__(self, dimensions, temperature=15):
		ThermalObject.__init__(self, geothermal.ThermalConstants.SpecificHeat.soil, geothermal.ThermalConstants.Density.soil, geothermal.ThermalConstants.Conductivity.soil, geothermal.ThermalConstants.Emissivity.soil, dimensions, temperature)

class Air(ThermalObject):

	def __init__(self, dimensions, temperature=15):
		ThermalObject.__init__(self, geothermal.ThermalConstants.SpecificHeat.air, geothermal.ThermalConstants.Density.air, geothermal.ThermalConstants.Conductivity.air, geothermal.ThermalConstants.Emissivity.blackBody, dimensions, temperature)


class Aluminum(ThermalObject):

	def __init__(self, dimensions, temperature=15):
		ThermalObject.__init__(self, geothermal.ThermalConstants.SpecificHeat.aluminum, geothermal.ThermalConstants.Density.aluminum, geothermal.ThermalConstants.Conductivity.aluminum, geothermal.ThermalConstants.Emissivity.aluminum, dimensions, temperature)

